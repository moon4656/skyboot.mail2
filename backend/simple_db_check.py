#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 데이터베이스 상태 확인
"""

import psycopg2
from datetime import datetime

def main():
    """메인 함수"""
    print(f"🔍 간단한 데이터베이스 상태 확인")
    print("=" * 50)
    
    user_uuid = '3b959219-da10-42bb-9693-0aa3ed502cd3'  # user01의 UUID
    
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="skyboot_mail",
            user="postgres",
            password="postgres"
        )
        cursor = conn.cursor()
        
        # 1. 폴더별 메일 수 확인
        print(f"\n📁 user01 폴더별 메일 수:")
        cursor.execute("""
            SELECT 
                mf.folder_type,
                COUNT(mif.mail_uuid) as total,
                COUNT(CASE WHEN mif.is_read = false THEN 1 END) as unread
            FROM mail_folders mf
            LEFT JOIN mail_in_folders mif ON mf.folder_uuid = mif.folder_uuid
            WHERE mf.user_uuid = %s
            GROUP BY mf.folder_type
            ORDER BY mf.folder_type;
        """, (user_uuid,))
        
        folders = cursor.fetchall()
        for folder in folders:
            folder_type = folder[0]
            total = folder[1]
            unread = folder[2]
            print(f"  {folder_type}: 총 {total}개, 읽지않음 {unread}개")
        
        # 2. INBOX의 읽지 않은 메일 확인
        print(f"\n📧 INBOX 읽지 않은 메일 상세:")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM mails m
            JOIN mail_in_folders mif ON m.mail_uuid = mif.mail_uuid
            JOIN mail_folders mf ON mif.folder_uuid = mf.folder_uuid
            WHERE mf.user_uuid = %s 
            AND mf.folder_type = 'inbox'
            AND mif.is_read = false;
        """, (user_uuid,))
        
        unread_count = cursor.fetchone()[0]
        print(f"  읽지 않은 메일: {unread_count}개")
        
        # 3. 읽지 않은 메일이 없다면 테스트 메일 생성
        if unread_count == 0:
            print(f"\n📝 테스트용 읽지 않은 메일 생성 중...")
            
            # INBOX 폴더 UUID 조회
            cursor.execute("""
                SELECT folder_uuid FROM mail_folders 
                WHERE user_uuid = %s AND folder_type = 'inbox'
            """, (user_uuid,))
            
            inbox_result = cursor.fetchone()
            if inbox_result:
                inbox_uuid = inbox_result[0]
                
                # SENT 폴더의 메일 중 2개를 INBOX로 복사
                cursor.execute("""
                    SELECT m.mail_uuid 
                    FROM mails m
                    JOIN mail_in_folders mif ON m.mail_uuid = mif.mail_uuid
                    JOIN mail_folders mf ON mif.folder_uuid = mf.folder_uuid
                    WHERE mf.user_uuid = %s AND mf.folder_type = 'sent'
                    LIMIT 2
                """, (user_uuid,))
                
                sent_mails = cursor.fetchall()
                
                for mail in sent_mails:
                    mail_uuid = mail[0]
                    
                    # INBOX에 이미 있는지 확인
                    cursor.execute("""
                        SELECT COUNT(*) FROM mail_in_folders mif
                        JOIN mail_folders mf ON mif.folder_uuid = mf.folder_uuid
                        WHERE mif.mail_uuid = %s AND mf.folder_type = 'inbox' AND mf.user_uuid = %s
                    """, (mail_uuid, user_uuid))
                    
                    exists = cursor.fetchone()[0] > 0
                    
                    if not exists:
                        # INBOX에 메일 추가 (읽지 않음 상태로)
                        cursor.execute("""
                            INSERT INTO mail_in_folders (mail_uuid, folder_uuid, user_uuid, is_read, created_at)
                            VALUES (%s, %s, %s, false, NOW())
                        """, (mail_uuid, inbox_uuid, user_uuid))
                        print(f"  ✅ 메일 추가: {mail_uuid[:8]}...")
                    else:
                        # 이미 있다면 읽지 않음 상태로 변경
                        cursor.execute("""
                            UPDATE mail_in_folders 
                            SET is_read = false
                            WHERE mail_uuid = %s AND folder_uuid = %s
                        """, (mail_uuid, inbox_uuid))
                        print(f"  🔄 메일 상태 변경: {mail_uuid[:8]}...")
                
                conn.commit()
                print(f"  ✅ 테스트 메일 생성 완료!")
                
                # 다시 확인
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM mails m
                    JOIN mail_in_folders mif ON m.mail_uuid = mif.mail_uuid
                    JOIN mail_folders mf ON mif.folder_uuid = mf.folder_uuid
                    WHERE mf.user_uuid = %s 
                    AND mf.folder_type = 'inbox'
                    AND mif.is_read = false;
                """, (user_uuid,))
                
                new_unread_count = cursor.fetchone()[0]
                print(f"  📊 생성 후 읽지 않은 메일: {new_unread_count}개")
        
        cursor.close()
        conn.close()
        
        print(f"\n✅ 데이터베이스 확인 완료!")
        
    except Exception as e:
        print(f"❌ 데이터베이스 확인 실패: {e}")

if __name__ == "__main__":
    main()