"""
현재 사용자를 MailUser 테이블에 등록하고 기본 조직에 연결하는 스크립트
"""
import psycopg2
import uuid
from datetime import datetime

# 데이터베이스 연결 설정
DB_CONFIG = {
    'host': 'localhost',
    'database': 'skyboot_mail',
    'user': 'postgres',
    'password': 'safe70!!',
    'port': '5432',
    'client_encoding': 'utf8'
}

def setup_mail_user():
    """현재 사용자를 MailUser 테이블에 등록합니다."""
    
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("🚀 MailUser 설정 시작")
        print("=" * 60)
        
        # 1. 기존 users 테이블에서 사용자 정보 조회
        print("📋 1. 기존 사용자 정보 조회...")
        cursor.execute("SELECT id, email FROM users WHERE email = 'user01@example.com';")
        user_data = cursor.fetchone()
        
        if not user_data:
            print("❌ user01@example.com 사용자를 찾을 수 없습니다.")
            return
        
        user_id, email = user_data
        # 새로운 UUID 생성
        user_uuid = str(uuid.uuid4())
        print(f"✅ 사용자 발견: {email} (ID: {user_id}, 새 UUID: {user_uuid})")
        
        # 2. 기본 조직 확인
        print("📋 2. 기본 조직 확인...")
        cursor.execute("SELECT org_id FROM organizations WHERE org_code = 'DEFAULT';")
        org_data = cursor.fetchone()
        
        if not org_data:
            print("❌ 기본 조직을 찾을 수 없습니다.")
            return
        
        org_id = org_data[0]
        print(f"✅ 기본 조직 발견: {org_id}")
        
        # 3. MailUser 테이블에 사용자 등록 확인
        print("📋 3. MailUser 등록 확인...")
        cursor.execute("""
            SELECT user_uuid FROM mail_users 
            WHERE user_uuid = %s AND org_id = %s;
        """, (user_uuid, org_id))
        
        existing_mail_user = cursor.fetchone()
        
        if existing_mail_user:
            print(f"✅ 이미 MailUser로 등록되어 있습니다: {user_uuid}")
        else:
            # 4. MailUser 테이블에 사용자 등록
            print("📋 4. MailUser 테이블에 사용자 등록...")
            cursor.execute("""
                INSERT INTO mail_users (
                    user_id, user_uuid, org_id, email, password_hash, 
                    display_name, is_active, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                );
            """, (
                f"user_{user_uuid[:8]}",  # user_id
                user_uuid,               # user_uuid
                org_id,                  # org_id
                email,                   # email
                "hashed_password",       # password_hash (임시)
                "User 01",               # display_name
                True,                    # is_active
                datetime.now(),          # created_at
                datetime.now()           # updated_at
            ))
            print(f"✅ MailUser 등록 완료: {email}")
        
        # 5. 추가 테스트 사용자 등록 (moon4656@gmail.com)
        print("📋 5. 추가 테스트 사용자 등록...")
        test_user_uuid = str(uuid.uuid4())
        test_email = "moon4656@gmail.com"
        
        # 기존 사용자 확인
        cursor.execute("SELECT user_uuid FROM mail_users WHERE email = %s;", (test_email,))
        existing_test_user = cursor.fetchone()
        
        if not existing_test_user:
            cursor.execute("""
                INSERT INTO mail_users (
                    user_id, user_uuid, org_id, email, password_hash, 
                    display_name, is_active, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                );
            """, (
                f"user_{test_user_uuid[:8]}",  # user_id
                test_user_uuid,                # user_uuid
                org_id,                        # org_id
                test_email,                    # email
                "external_user",               # password_hash
                "Moon Test User",              # display_name
                True,                          # is_active
                datetime.now(),                # created_at
                datetime.now()                 # updated_at
            ))
            print(f"✅ 테스트 사용자 등록 완료: {test_email}")
        else:
            print(f"✅ 테스트 사용자 이미 존재: {test_email}")
        
        # 변경사항 커밋
        conn.commit()
        
        # 6. 등록된 MailUser 확인
        print("\n📊 등록된 MailUser 확인:")
        cursor.execute("""
            SELECT user_id, email, display_name, is_active, org_id
            FROM mail_users 
            ORDER BY created_at;
        """)
        mail_users = cursor.fetchall()
        
        for user in mail_users:
            print(f"   - {user[0]}: {user[1]} ({user[2]}) - 활성: {user[3]}, 조직: {user[4]}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 MailUser 설정 완료!")
        
    except Exception as e:
        print(f"❌ MailUser 설정 실패: {e}")
        import traceback
        traceback.print_exc()

def main():
    """메인 함수"""
    print("🚀 MailUser 설정 시작")
    print(f"⏰ 시작 시간: {datetime.now()}")
    
    setup_mail_user()
    
    print(f"\n⏰ 완료 시간: {datetime.now()}")

if __name__ == "__main__":
    main()