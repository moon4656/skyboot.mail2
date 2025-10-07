#!/usr/bin/env python3
"""
test@example.com 사용자의 로그인 정보 확인 스크립트
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def check_test_example_user():
    """test@example.com 사용자의 로그인 정보를 확인합니다."""
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
        
        print("=== test@example.com 사용자 로그인 정보 확인 ===\n")
        
        # users 테이블에서 test@example.com 사용자 확인
        cursor.execute("""
            SELECT user_id, email, username, is_active, role, created_at
            FROM users 
            WHERE email = 'test@example.com'
        """)
        
        user = cursor.fetchone()
        if user:
            print("✅ users 테이블에서 발견:")
            print(f"  - 사용자 ID: {user['user_id']}")
            print(f"  - 이메일: {user['email']}")
            print(f"  - 사용자명: {user['username']}")
            print(f"  - 활성화: {user['is_active']}")
            print(f"  - 역할: {user['role']}")
            print(f"  - 생성일: {user['created_at']}")
        else:
            print("❌ test@example.com 사용자를 users 테이블에서 찾을 수 없습니다.")
        
        # mail_users 테이블에서도 확인
        cursor.execute("""
            SELECT user_uuid, email, display_name, is_active, created_at
            FROM mail_users 
            WHERE email = 'test@example.com'
        """)
        
        mail_user = cursor.fetchone()
        if mail_user:
            print("\n✅ mail_users 테이블에서 발견:")
            print(f"  - UUID: {mail_user['user_uuid']}")
            print(f"  - 이메일: {mail_user['email']}")
            print(f"  - 표시명: {mail_user['display_name']}")
            print(f"  - 활성화: {mail_user['is_active']}")
            print(f"  - 생성일: {mail_user['created_at']}")
        else:
            print("\n❌ test@example.com 사용자를 mail_users 테이블에서 찾을 수 없습니다.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    check_test_example_user()