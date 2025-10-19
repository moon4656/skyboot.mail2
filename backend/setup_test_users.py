#!/usr/bin/env python3
"""
테스트용 사용자 및 조직 설정 스크립트 (정확한 스키마 기반)
addressbook 테스트에 필요한 admin01, user01 사용자를 확인하고 조직을 연결합니다.
"""

import psycopg2
import bcrypt
import uuid
from datetime import datetime
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

def setup_test_data():
    """테스트용 조직과 사용자를 설정합니다."""
    try:
        print("🏢 테스트 데이터 설정 시작...")
        
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            port=settings.DB_PORT
        )
        cursor = conn.cursor()
        
        # 1. 조직 확인 및 생성
        print("1️⃣ 조직 확인 중...")
        cursor.execute("SELECT org_id, org_code, name, domain FROM organizations WHERE domain = %s", ("test.skyboot.mail",))
        org = cursor.fetchone()
        
        if org:
            org_id = org[0]
            print(f"✅ 기존 조직 사용: ID={org[0]}, 코드={org[1]}, 이름={org[2]}, 도메인={org[3]}")
        else:
            # 새 조직 생성
            org_id = str(uuid.uuid4())
            org_code = "test"
            cursor.execute("""
                INSERT INTO organizations (
                    org_id, org_code, name, display_name, description, domain, subdomain,
                    admin_email, admin_name, max_users, max_storage_gb, max_emails_per_day,
                    status, is_active, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING org_id, org_code, name, domain
            """, (
                org_id,
                org_code,
                "테스트 조직",
                "Test Organization",
                "addressbook 테스트용 조직",
                "test.skyboot.mail",
                "test",
                "admin@test.skyboot.mail",
                "Test Admin",
                100,  # max_users
                5,    # max_storage_gb
                500,  # max_emails_per_day
                "active",
                True,
                datetime.now(),
                datetime.now()
            ))
            
            new_org = cursor.fetchone()
            org_id = new_org[0]
            conn.commit()
            print(f"✅ 새 조직 생성: ID={new_org[0]}, 코드={new_org[1]}, 이름={new_org[2]}, 도메인={new_org[3]}")
        
        # 2. 기존 사용자 확인
        print("2️⃣ 기존 사용자 확인 중...")
        cursor.execute("SELECT user_id, email, org_id FROM users WHERE user_id IN (%s, %s)", ("admin01", "user01"))
        existing_users = cursor.fetchall()
        
        for user in existing_users:
            print(f"   - {user[0]} ({user[1]}) - 조직: {user[2]}")
        
        # 3. 사용자들을 테스트 조직에 연결
        print("3️⃣ 사용자 조직 연결 확인 중...")
        
        # admin01 사용자 조직 연결
        cursor.execute("SELECT user_id, org_id FROM users WHERE user_id = %s", ("admin01",))
        admin_user = cursor.fetchone()
        
        if admin_user:
            if admin_user[1] != org_id:
                cursor.execute("UPDATE users SET org_id = %s WHERE user_id = %s", (org_id, "admin01"))
                conn.commit()
                print(f"✅ admin01 사용자를 조직 {org_id}에 연결했습니다.")
            else:
                print(f"✅ admin01 사용자가 이미 조직 {org_id}에 연결되어 있습니다.")
        
        # user01 사용자 조직 연결
        cursor.execute("SELECT user_id, org_id FROM users WHERE user_id = %s", ("user01",))
        regular_user = cursor.fetchone()
        
        if regular_user:
            if regular_user[1] != org_id:
                cursor.execute("UPDATE users SET org_id = %s WHERE user_id = %s", (org_id, "user01"))
                conn.commit()
                print(f"✅ user01 사용자를 조직 {org_id}에 연결했습니다.")
            else:
                print(f"✅ user01 사용자가 이미 조직 {org_id}에 연결되어 있습니다.")
        
        # 4. 최종 확인
        print("4️⃣ 최종 사용자 상태 확인:")
        cursor.execute("""
            SELECT u.user_id, u.email, u.org_id, o.name as org_name
            FROM users u
            LEFT JOIN organizations o ON u.org_id = o.org_id
            WHERE u.user_id IN (%s, %s)
        """, ("admin01", "user01"))
        
        final_users = cursor.fetchall()
        for user in final_users:
            print(f"   - {user[0]} ({user[1]}) - 조직: {user[3]} ({user[2]})")
        
        # 5. 연락처 및 그룹 테이블 확인
        print("5️⃣ addressbook 테이블 확인:")
        
        # contacts 테이블 데이터 확인
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE org_id = %s", (org_id,))
        contact_count = cursor.fetchone()[0]
        print(f"   - contacts: {contact_count}개")
        
        # contact_groups 테이블 확인
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'contact_groups'
        """)
        groups_table = cursor.fetchone()
        
        if groups_table:
            cursor.execute("SELECT COUNT(*) FROM contact_groups WHERE org_id = %s", (org_id,))
            group_count = cursor.fetchone()[0]
            print(f"   - contact_groups: {group_count}개")
        else:
            print("   - contact_groups: 테이블 없음")
        
        # 6. 테스트에 사용할 조직 ID 출력
        print(f"\n🎯 테스트에 사용할 조직 ID: {org_id}")
        print(f"🎯 테스트에 사용할 조직 코드: {org_code if 'org_code' in locals() else 'test'}")
        
        cursor.close()
        conn.close()
        print("🎉 테스트 데이터 설정 완료!")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 데이터 설정 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = setup_test_data()
    if not success:
        sys.exit(1)