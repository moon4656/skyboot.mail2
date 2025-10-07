#!/usr/bin/env python3
"""
특정 메일 ID의 수신자 정보 확인 스크립트
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def check_mail_recipients():
    """특정 메일 ID의 수신자 정보를 확인합니다."""
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
        
        mail_id = "20251005_235140_009e55f6a7f6"
        
        print(f"=== 메일 ID {mail_id}의 수신자 정보 확인 ===\n")
        
        # 1. 메일 기본 정보 확인
        print("1. 메일 기본 정보:")
        cursor.execute("""
            SELECT m.mail_uuid, m.subject, m.status, m.sent_at, m.created_at,
                   mu.email as sender_email, mu.user_uuid as sender_uuid
            FROM mails m
            LEFT JOIN mail_users mu ON m.sender_uuid = mu.user_uuid
            WHERE m.mail_uuid = %s
        """, (mail_id,))
        
        mail_info = cursor.fetchone()
        if mail_info:
            print(f"  - 메일 ID: {mail_info['mail_uuid']}")
            print(f"  - 제목: {mail_info['subject']}")
            print(f"  - 발송자: {mail_info['sender_email']} ({mail_info['sender_uuid']})")
            print(f"  - 상태: {mail_info['status']}")
            print(f"  - 발송시간: {mail_info['sent_at']}")
            print(f"  - 생성시간: {mail_info['created_at']}")
        else:
            print(f"  메일 ID {mail_id}를 찾을 수 없습니다.")
            return
        
        # 2. 수신자 정보 확인
        print(f"\n2. 수신자 정보:")
        cursor.execute("""
            SELECT mr.recipient_email, mr.recipient_type, mr.recipient_uuid,
                   mu.user_uuid, mu.email as mail_user_email
            FROM mail_recipients mr
            LEFT JOIN mail_users mu ON mr.recipient_uuid = mu.user_uuid
            WHERE mr.mail_uuid = %s
        """, (mail_id,))
        
        recipients = cursor.fetchall()
        if recipients:
            for recipient in recipients:
                print(f"  - 수신자 이메일: {recipient['recipient_email']}")
                print(f"    타입: {recipient['recipient_type']}")
                print(f"    수신자 UUID: {recipient['recipient_uuid']}")
                print(f"    메일 사용자 이메일: {recipient['mail_user_email']}")
                print()
        else:
            print("  수신자 정보가 없습니다.")
        
        # 3. mail_in_folders에서 해당 메일 확인
        print(f"\n3. mail_in_folders에서 해당 메일 확인:")
        cursor.execute("""
            SELECT mif.user_uuid, mif.folder_uuid, mif.is_read, mif.read_at,
                   mu.email as user_email, mf.name as folder_name
            FROM mail_in_folders mif
            LEFT JOIN mail_users mu ON mif.user_uuid = mu.user_uuid
            LEFT JOIN mail_folders mf ON mif.folder_uuid = mf.folder_uuid
            WHERE mif.mail_uuid = %s
        """, (mail_id,))
        
        mail_in_folders = cursor.fetchall()
        if mail_in_folders:
            for mif in mail_in_folders:
                print(f"  - 사용자: {mif['user_email']} ({mif['user_uuid']})")
                print(f"    폴더: {mif['folder_name']}")
                print(f"    읽음 상태: {mif['is_read']}")
                print(f"    읽은 시간: {mif['read_at']}")
                print()
        else:
            print("  mail_in_folders에 데이터가 없습니다.")
        
        # 4. 수신자 중에서 users 테이블에 있는 사용자 확인
        print(f"\n4. 수신자 중 로그인 가능한 사용자 확인:")
        for recipient in recipients:
            cursor.execute("""
                SELECT user_id, email, username, is_active
                FROM users
                WHERE email = %s
            """, (recipient['recipient_email'],))
            
            user = cursor.fetchone()
            if user:
                print(f"  - 이메일: {user['email']}")
                print(f"    사용자 ID: {user['user_id']}")
                print(f"    사용자명: {user['username']}")
                print(f"    활성화: {user['is_active']}")
                print()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    check_mail_recipients()