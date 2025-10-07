#!/usr/bin/env python3
"""
수신자 사용자로 메일 읽음 처리 API 테스트

testuser_folder 사용자로 로그인하여 받은 메일의 읽음 상태를 변경하는 테스트
"""
import requests
import json
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# 설정
BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api/v1"

# 테스트 사용자 정보
TEST_USER = {
    "user_id": "testuser_folder",
    "password": "password"
}

# 데이터베이스 연결 정보
DB_CONFIG = {
    "host": "localhost",
    "database": "skyboot_mail",
    "user": "postgres",
    "password": "postgres",
    "port": 5432
}

def login_user(user_id: str, password: str) -> str:
    """사용자 로그인 및 토큰 획득"""
    print(f"🔐 로그인 시도: {user_id}")
    
    login_data = {
        "user_id": user_id,
        "password": password
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   로그인 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if "access_token" in result:
                print(f"✅ 로그인 성공: 토큰 획득")
                return result["access_token"]
            else:
                print(f"❌ 로그인 실패: 토큰이 응답에 없음")
                print(f"   응답 내용: {result}")
                return None
        else:
            print(f"❌ 로그인 실패: {response.status_code}")
            print(f"   응답 내용: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 로그인 요청 오류: {e}")
        return None

def get_inbox_mails(token: str):
    """받은 메일함 조회"""
    print(f"\n📥 받은 메일함 조회")
    print("-" * 50)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{API_BASE}/mail/inbox",
            headers=headers,
            params={"page": 1, "limit": 10}
        )
        
        print(f"   응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success") and result.get("data", {}).get("mails"):
                mails = result["data"]["mails"]
                print(f"📧 받은 메일 {len(mails)}개:")
                
                for i, mail in enumerate(mails, 1):
                    mail_uuid = mail.get("mail_uuid", "Unknown")
                    subject = mail.get("subject", "제목 없음")
                    sender = mail.get("sender_email", "발송자 불명")
                    is_read = mail.get("is_read", False)
                    
                    print(f"   {i}. {subject}")
                    print(f"      UUID: {mail_uuid}")
                    print(f"      발송자: {sender}")
                    print(f"      읽음상태: {'읽음' if is_read else '읽지않음'}")
                    print()
                
                return mails[0]["mail_uuid"] if mails else None
            else:
                print(f"📭 받은 메일이 없습니다.")
                return None
        else:
            print(f"❌ 받은 메일함 조회 실패: {response.status_code}")
            print(f"   응답 내용: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 받은 메일함 조회 오류: {e}")
        return None

def mark_mail_read(token: str, mail_uuid: str):
    """메일 읽음 처리"""
    print(f"\n📖 메일 읽음 처리: {mail_uuid}")
    print("-" * 50)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/mail/{mail_uuid}/read",
            headers=headers
        )
        
        print(f"📊 읽음 처리 API 응답:")
        print(f"   상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   응답 내용: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"   응답 내용: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 읽음 처리 API 오류: {e}")
        return False

def check_database_status(mail_uuid: str, user_email: str):
    """데이터베이스에서 읽음 상태 확인"""
    print(f"\n🔍 데이터베이스 상태 확인")
    print("-" * 50)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # MailInFolder 테이블에서 읽음 상태 확인
        query = """
            SELECT 
                mif.mail_uuid,
                mif.is_read,
                mif.read_at,
                mu.email as user_email,
                mf.name as folder_name
            FROM mail_in_folders mif
            JOIN mail_users mu ON mif.user_uuid = mu.user_uuid
            JOIN mail_folders mf ON mif.folder_uuid = mf.folder_uuid
            WHERE mif.mail_uuid = %s AND mu.email = %s
        """
        
        cursor.execute(query, (mail_uuid, user_email))
        result = cursor.fetchone()
        
        if result:
            print(f"   사용자: {result['user_email']}")
            print(f"   폴더: {result['folder_name']}")
            print(f"   읽음 상태: {'읽음' if result['is_read'] else '읽지 않음'}")
            print(f"   읽은 시간: {result['read_at'] or '읽지 않음'}")
            return result['is_read']
        else:
            print(f"   ❌ 해당 메일을 찾을 수 없습니다.")
            return None
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 데이터베이스 조회 오류: {e}")
        return None

def main():
    """메인 테스트 함수"""
    print("=" * 60)
    print("🧪 수신자 메일 읽음 처리 API 테스트")
    print("=" * 60)
    print(f"시작 시간: {datetime.now()}")
    print()
    
    # 1. 로그인
    print("1️⃣ 사용자 로그인")
    print("-" * 50)
    token = login_user(TEST_USER["user_id"], TEST_USER["password"])
    
    if not token:
        print("❌ 로그인 실패로 테스트 중단")
        return
    
    # 2. 받은 메일함 조회
    mail_uuid = get_inbox_mails(token)
    
    if not mail_uuid:
        print("❌ 테스트할 메일이 없어서 테스트 중단")
        return
    
    # 3. 읽음 처리 전 데이터베이스 상태 확인
    print(f"\n3️⃣ 읽음 처리 전 데이터베이스 상태")
    print("-" * 50)
    before_status = check_database_status(mail_uuid, "testuser_folder@example.com")
    
    # 4. 메일 읽음 처리
    print(f"\n4️⃣ 메일 읽음 처리 API 호출")
    print("-" * 50)
    read_success = mark_mail_read(token, mail_uuid)
    
    if not read_success:
        print("❌ 읽음 처리 실패로 테스트 중단")
        return
    
    # 5. 읽음 처리 후 데이터베이스 상태 확인
    print(f"\n5️⃣ 읽음 처리 후 데이터베이스 상태")
    print("-" * 50)
    after_status = check_database_status(mail_uuid, "testuser_folder@example.com")
    
    # 6. 결과 요약
    print(f"\n6️⃣ 테스트 결과 요약")
    print("-" * 50)
    print(f"   읽음 처리 API: {'성공' if read_success else '실패'}")
    print(f"   데이터베이스 상태 변화: {before_status} → {after_status}")
    
    if before_status is not None and after_status is not None:
        if before_status != after_status and after_status == True:
            print(f"   ✅ 읽음 상태가 정상적으로 변경되었습니다!")
        elif before_status == after_status == True:
            print(f"   ℹ️ 이미 읽음 상태였습니다.")
        else:
            print(f"   ❌ 읽음 상태 변경에 문제가 있습니다.")
    
    print(f"\n🏁 테스트 완료")
    print("=" * 60)
    print(f"종료 시간: {datetime.now()}")

if __name__ == "__main__":
    main()