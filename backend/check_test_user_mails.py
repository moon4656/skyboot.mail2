#!/usr/bin/env python3
"""
test@skyboot.kr 사용자의 메일 정보 확인 스크립트
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def check_test_user_mails():
    """test@skyboot.kr 사용자의 메일 정보를 확인합니다."""
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'skyboot_mail'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'password'),
            port=os.getenv('DB_PORT', '5432')
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("=== test@skyboot.kr 사용자 메일 정보 확인 ===\n")
        
        # 1. test@skyboot.kr 사용자의 mail_users 정보 확인
        print("1. test@skyboot.kr 사용자의 mail_users 정보:")
        cursor.execute("""
            SELECT user_uuid, email, display_name, org_id, is_active
            FROM mail_users 
            WHERE email = 'test@skyboot.kr'
        """)
        
        mail_user = cursor.fetchone()
        if mail_user:
            print(f"  - UUID: {mail_user['user_uuid']}")
            print(f"  - 이메일: {mail_user['email']}")
            print(f"  - 표시명: {mail_user['display_name']}")
            print(f"  - 조직 ID: {mail_user['org_id']}")
            print(f"  - 활성화: {mail_user['is_active']}")
            
            user_uuid = mail_user['user_uuid']
            
            # 2. 해당 사용자가 수신한 메일 확인
            print(f"\n2. test@skyboot.kr 사용자가 수신한 메일:")
            cursor.execute("""
                SELECT DISTINCT m.mail_uuid, m.subject, m.status, m.sent_at, m.created_at,
                       mu.email as sender_email
                FROM mails m
                JOIN mail_recipients mr ON m.mail_uuid = mr.mail_uuid
                LEFT JOIN mail_users mu ON m.sender_uuid = mu.user_uuid
                WHERE mr.recipient_email = 'test@skyboot.kr'
                ORDER BY m.created_at DESC
                LIMIT 10
            """)
            
            received_mails = cursor.fetchall()
            if received_mails:
                for mail in received_mails:
                    print(f"  - 메일 ID: {mail['mail_uuid']}")
                    print(f"    제목: {mail['subject']}")
                    print(f"    발송자: {mail['sender_email']}")
                    print(f"    상태: {mail['status']}")
                    print(f"    발송시간: {mail['sent_at']}")
                    print(f"    생성시간: {mail['created_at']}")
                    print()
            else:
                print("  수신한 메일이 없습니다.")
            
            # 3. 해당 사용자의 폴더 정보 확인
            print(f"\n3. test@skyboot.kr 사용자의 폴더 정보:")
            cursor.execute("""
                SELECT folder_uuid, name, folder_type, is_system, created_at
                FROM mail_folders 
                WHERE user_uuid = %s
                ORDER BY created_at
            """, (user_uuid,))
            
            folders = cursor.fetchall()
            if folders:
                for folder in folders:
                    print(f"  - 폴더 UUID: {folder['folder_uuid']}")
                    print(f"    이름: {folder['name']}")
                    print(f"    타입: {folder['folder_type']}")
                    print(f"    시스템 폴더: {folder['is_system']}")
                    print(f"    생성시간: {folder['created_at']}")
                    print()
            else:
                print("  폴더가 없습니다.")
            
            # 4. mail_in_folders에서 해당 사용자의 메일 확인
            print(f"\n4. test@skyboot.kr 사용자의 mail_in_folders 정보:")
            cursor.execute("""
                SELECT mif.mail_uuid, mif.folder_uuid, mif.is_read, mif.read_at, mif.created_at,
                       m.subject, mf.name as folder_name
                FROM mail_in_folders mif
                JOIN mails m ON mif.mail_uuid = m.mail_uuid
                JOIN mail_folders mf ON mif.folder_uuid = mf.folder_uuid
                WHERE mif.user_uuid = %s
                ORDER BY mif.created_at DESC
                LIMIT 10
            """, (user_uuid,))
            
            mail_in_folders = cursor.fetchall()
            if mail_in_folders:
                for mif in mail_in_folders:
                    print(f"  - 메일 ID: {mif['mail_uuid']}")
                    print(f"    제목: {mif['subject']}")
                    print(f"    폴더: {mif['folder_name']}")
                    print(f"    읽음 상태: {mif['is_read']}")
                    print(f"    읽은 시간: {mif['read_at']}")
                    print(f"    생성시간: {mif['created_at']}")
                    print()
            else:
                print("  mail_in_folders에 데이터가 없습니다.")
                
        else:
            print("  test@skyboot.kr 사용자를 mail_users 테이블에서 찾을 수 없습니다.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    check_test_user_mails()