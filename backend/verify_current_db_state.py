#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
현재 데이터베이스 상태 확인

읽지 않은 메일 상태를 다시 확인하고 필요시 테스트 데이터를 생성합니다.
"""

import psycopg2
from datetime import datetime

# 데이터베이스 연결 설정
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "skyboot_mail",
    "user": "postgres",
    "password": "postgres",
    "client_encoding": "utf8"
}

def get_db_connection():
    """데이터베이스 연결 생성"""
    return psycopg2.connect(**DB_CONFIG)

def check_user01_folders():
    """user01의 폴더 상태 확인"""
    print(f"\n📁 user01 폴더 상태 확인")
    print("=" * 50)
    
    user_uuid = '3b959219-da10-42bb-9693-0aa3ed502cd3'  # user01의 UUID
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 폴더별 메일 수 확인
        query = """
            SELECT 
                mf.name,
                mf.folder_type,
                COUNT(mif.mail_uuid) as total_mails,
                COUNT(CASE WHEN mif.is_read = false THEN 1 END) as unread_mails
            FROM mail_folders mf
            LEFT JOIN mail_in_folders mif ON mf.folder_uuid = mif.folder_uuid
            WHERE mf.user_uuid = %s
            GROUP BY mf.folder_uuid, mf.name, mf.folder_type
            ORDER BY mf.folder_type;
        """
        
        cursor.execute(query, (user_uuid,))
        folders = cursor.fetchall()
        
        print(f"📊 user01의 폴더별 메일 현황:")
        for folder in folders:
            name = folder[0]
            folder_type = folder[1]
            total = folder[2]
            unread = folder[3]
            print(f"  📁 {name} ({folder_type}): 총 {total}개, 읽지않음 {unread}개")
        
        cursor.close()
        conn.close()
        
        return folders
        
    except Exception as e:
        print(f"❌ 폴더 상태 확인 실패: {e}")
        return []

def check_inbox_details():
    """INBOX의 상세 메일 정보 확인"""
    print(f"\n📧 INBOX 상세 메일 정보")
    print("=" * 50)
    
    user_uuid = '3b959219-da10-42bb-9693-0aa3ed502cd3'  # user01의 UUID
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # INBOX의 모든 메일 확인
        query = """
            SELECT 
                m.mail_uuid,
                m.subject,
                m.created_at,
                mif.is_read,
                mif.created_at as folder_added_at
            FROM mails m
            JOIN mail_in_folders mif ON m.mail_uuid = mif.mail_uuid
            JOIN mail_folders mf ON mif.folder_uuid = mf.folder_uuid
            WHERE mf.user_uuid = %s 
            AND mf.folder_type = 'inbox'
            ORDER BY m.created_at DESC;
        """
        
        cursor.execute(query, (user_uuid,))
        mails = cursor.fetchall()
        
        print(f"📧 INBOX의 모든 메일: {len(mails)}개")
        
        if mails:
            print(f"\n📋 메일 목록:")
            for i, mail in enumerate(mails, 1):
                mail_uuid = str(mail[0])[:8] if mail[0] else "N/A"
                subject = str(mail[1]) if mail[1] else "No Subject"
                created_at = str(mail[2]) if mail[2] else "Unknown"
                is_read = mail[3]
                folder_added_at = str(mail[4]) if mail[4] else "Unknown"
                
                status = "읽음" if is_read else "읽지않음"
                print(f"  {i}. {subject}")
                print(f"     UUID: {mail_uuid}...")
                print(f"     생성일: {created_at}")
                print(f"     상태: {status}")
                print(f"     폴더추가일: {folder_added_at}")
                print()
        else:
            print(f"📭 INBOX에 메일이 없습니다.")
        
        cursor.close()
        conn.close()
        
        return len([m for m in mails if not m[3]])  # 읽지 않은 메일 수
        
    except Exception as e:
        print(f"❌ INBOX 상세 정보 확인 실패: {e}")
        return 0

def create_test_unread_mail():
    """테스트용 읽지 않은 메일 생성"""
    print(f"\n📝 테스트용 읽지 않은 메일 생성")
    print("=" * 50)
    
    user_uuid = '3b959219-da10-42bb-9693-0aa3ed502cd3'  # user01의 UUID
    org_id = '3856a8c1-84a4-4019-9133-655cacab4bc9'  # user01의 조직 ID
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # INBOX 폴더 UUID 조회
        cursor.execute("""
            SELECT folder_uuid FROM mail_folders 
            WHERE user_uuid = %s AND folder_type = 'inbox'
        """, (user_uuid,))
        
        inbox_result = cursor.fetchone()
        if not inbox_result:
            print(f"❌ INBOX 폴더를 찾을 수 없습니다.")
            return False
        
        inbox_uuid = inbox_result[0]
        print(f"📁 INBOX UUID: {inbox_uuid}")
        
        # 기존 SENT 폴더의 메일 중 하나를 INBOX로 복사
        cursor.execute("""
            SELECT m.mail_uuid, m.subject 
            FROM mails m
            JOIN mail_in_folders mif ON m.mail_uuid = mif.mail_uuid
            JOIN mail_folders mf ON mif.folder_uuid = mf.folder_uuid
            WHERE mf.user_uuid = %s AND mf.folder_type = 'sent'
            LIMIT 2
        """, (user_uuid,))
        
        sent_mails = cursor.fetchall()
        
        if not sent_mails:
            print(f"❌ SENT 폴더에 복사할 메일이 없습니다.")
            return False
        
        print(f"📤 SENT 폴더에서 {len(sent_mails)}개 메일을 INBOX로 복사합니다.")
        
        for mail in sent_mails:
            mail_uuid = mail[0]
            subject = mail[1]
            
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
                
                print(f"  ✅ 메일 추가: {subject}")
            else:
                # 이미 있다면 읽지 않음 상태로 변경
                cursor.execute("""
                    UPDATE mail_in_folders 
                    SET is_read = false
                    WHERE mail_uuid = %s AND folder_uuid = %s
                """, (mail_uuid, inbox_uuid))
                
                print(f"  🔄 메일 상태 변경: {subject}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ 테스트 메일 생성 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 메일 생성 실패: {e}")
        return False

def main():
    """메인 함수"""
    print(f"🔍 현재 데이터베이스 상태 확인")
    print(f"시작 시간: {datetime.now()}")
    print("=" * 70)
    
    # 1. 폴더 상태 확인
    folders = check_user01_folders()
    
    # 2. INBOX 상세 정보 확인
    unread_count = check_inbox_details()
    
    # 3. 읽지 않은 메일이 없다면 테스트 메일 생성
    if unread_count == 0:
        print(f"\n⚠️ 읽지 않은 메일이 없습니다. 테스트용 메일을 생성합니다.")
        if create_test_unread_mail():
            print(f"\n🔄 메일 생성 후 다시 확인...")
            check_user01_folders()
            check_inbox_details()
    else:
        print(f"\n✅ 읽지 않은 메일이 {unread_count}개 있습니다.")
    
    print(f"\n🏁 확인 완료")
    print("=" * 70)
    print(f"종료 시간: {datetime.now()}")

if __name__ == "__main__":
    main()