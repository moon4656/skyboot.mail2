#!/usr/bin/env python3
"""
user01과 test 사용자 정보 확인 스크립트
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def check_user01_test_users():
    """user01과 test 사용자 정보를 확인합니다."""
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
        
        print("=== user01과 test 사용자 정보 확인 ===\n")
        
        # users 테이블에서 user01 또는 test 관련 사용자 검색
        print("1. users 테이블에서 user01/test 사용자 검색:")
        cursor.execute("""
            SELECT user_id, user_uuid, org_id, email, username, is_active, role, created_at
            FROM users 
            WHERE email LIKE '%user01%' OR email LIKE '%test%' OR username LIKE '%user01%' OR username LIKE '%test%'
            ORDER BY created_at DESC
        """)
        
        users = cursor.fetchall()
        if users:
            for user in users:
                print(f"  - 사용자 ID: {user['user_id']}")
                print(f"    UUID: {user['user_uuid']}")
                print(f"    조직 ID: {user['org_id']}")
                print(f"    이메일: {user['email']}")
                print(f"    사용자명: {user['username']}")
                print(f"    활성화: {user['is_active']}")
                print(f"    역할: {user['role']}")
                print(f"    생성일: {user['created_at']}")
                print()
        else:
            print("  user01 또는 test 관련 사용자를 찾을 수 없습니다.\n")
        
        # mail_users 테이블에서도 확인
        print("2. mail_users 테이블에서 user01/test 사용자 검색:")
        cursor.execute("""
            SELECT user_uuid, user_email, display_name, org_id, is_active, created_at
            FROM mail_users 
            WHERE user_email LIKE '%user01%' OR user_email LIKE '%test%' OR display_name LIKE '%user01%' OR display_name LIKE '%test%'
            ORDER BY created_at DESC
        """)
        
        mail_users = cursor.fetchall()
        if mail_users:
            for user in mail_users:
                print(f"  - UUID: {user['user_uuid']}")
                print(f"    이메일: {user['user_email']}")
                print(f"    표시명: {user['display_name']}")
                print(f"    조직 ID: {user['org_id']}")
                print(f"    활성화: {user['is_active']}")
                print(f"    생성일: {user['created_at']}")
                print()
        else:
            print("  user01 또는 test 관련 메일 사용자를 찾을 수 없습니다.\n")
        
        # 최근 생성된 사용자들도 확인
        print("3. 최근 생성된 사용자들 (users 테이블):")
        cursor.execute("""
            SELECT user_id, email, username, is_active, created_at
            FROM users 
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        recent_users = cursor.fetchall()
        for user in recent_users:
            print(f"  - {user['email']} ({user['username']}) - 활성화: {user['is_active']} - 생성일: {user['created_at']}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    check_user01_test_users()