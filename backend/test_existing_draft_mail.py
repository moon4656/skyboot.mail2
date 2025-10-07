#!/usr/bin/env python3
"""
기존 임시보관함 메일을 사용한 상세 조회 API 테스트
Terminal#1016-1020 오류 해결 확인
"""

import requests
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.user import get_db as get_user_db
from app.database.mail import get_db as get_mail_db
from app.model.mail_model import Mail
from app.model.user_model import User
from app.model.mail_model import MailUser
from sqlalchemy.orm import Session

# API 기본 설정
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def find_draft_mail_and_user():
    """데이터베이스에서 임시보관함 메일과 해당 사용자 찾기"""
    print("🔍 데이터베이스에서 임시보관함 메일 검색 중...")
    
    # 메일 데이터베이스에서 임시보관함 메일 찾기
    mail_db = next(get_mail_db())
    draft_mail = mail_db.query(Mail).filter(
        Mail.status == "draft"
    ).first()
    
    if not draft_mail:
        print("❌ 임시보관함 메일을 찾을 수 없습니다.")
        return None, None
    
    print(f"📧 임시보관함 메일 발견: {draft_mail.mail_uuid}")
    print(f"   - 제목: {draft_mail.subject}")
    print(f"   - 발송자 UUID: {draft_mail.sender_uuid}")
    print(f"   - 조직 ID: {draft_mail.org_id}")
    
    # 사용자 데이터베이스에서 해당 사용자 찾기
    user_db = next(get_user_db())
    mail_user = user_db.query(MailUser).filter(
        MailUser.user_uuid == draft_mail.sender_uuid
    ).first()
    
    if not mail_user:
        print("❌ 해당 메일의 발송자를 찾을 수 없습니다.")
        return draft_mail, None
    
    user = user_db.query(User).filter(
        User.user_uuid == mail_user.user_uuid
    ).first()
    
    if not user:
        print("❌ 사용자 정보를 찾을 수 없습니다.")
        return draft_mail, None
    
    print(f"👤 발송자 정보:")
    print(f"   - 사용자 ID: {user.user_id}")
    print(f"   - 이메일: {user.email}")
    print(f"   - 조직 ID: {user.org_id}")
    
    mail_db.close()
    user_db.close()
    
    return draft_mail, user

def test_draft_mail_detail_with_existing_mail():
    """기존 임시보관함 메일로 상세 조회 API 테스트"""
    print("🧪 기존 임시보관함 메일을 사용한 상세 조회 API 테스트 시작")
    print("📋 Terminal#1016-1020 오류 해결 확인")
    
    # 1. 데이터베이스에서 임시보관함 메일과 사용자 찾기
    draft_mail, user = find_draft_mail_and_user()
    if not draft_mail or not user:
        print("❌ 테스트할 임시보관함 메일 또는 사용자를 찾을 수 없습니다.")
        return False
    
    # 2. 해당 사용자로 로그인
    print(f"\n2️⃣ 사용자 로그인: {user.user_id}")
    login_data = {
        "user_id": user.user_id,
        "password": "test"  # 기본 테스트 패스워드
    }
    
    login_response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    print(f"로그인 응답 상태: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"❌ 로그인 실패: {login_response.text}")
        # 다른 패스워드 시도
        login_data["password"] = "test123"
        login_response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        print(f"대체 패스워드 로그인 시도: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"❌ 대체 패스워드로도 로그인 실패: {login_response.text}")
            return False
    
    login_result = login_response.json()
    access_token = login_result["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    print("✅ 로그인 성공")
    
    # 3. 임시보관함 메일 상세 조회 (수정된 API 테스트)
    print(f"\n3️⃣ 임시보관함 메일 상세 조회: {draft_mail.mail_uuid}")
    detail_response = requests.get(f"{API_BASE}/mail/drafts/{draft_mail.mail_uuid}", headers=headers)
    print(f"임시보관함 메일 상세 조회 상태: {detail_response.status_code}")
    print(f"응답 헤더: {dict(detail_response.headers)}")
    
    if detail_response.status_code == 200:
        print("✅ 임시보관함 메일 상세 조회 성공!")
        detail_data = detail_response.json()
        print(f"상세 정보: {json.dumps(detail_data, indent=2, ensure_ascii=False, default=str)}")
        
        # 4. 응답 구조 검증
        print("\n4️⃣ 응답 구조 검증")
        required_fields = ["success", "message", "data"]
        for field in required_fields:
            if field in detail_data:
                print(f"✅ {field} 필드 존재")
            else:
                print(f"❌ {field} 필드 누락")
                return False
        
        # data 내부 필드 검증
        if "data" in detail_data and isinstance(detail_data["data"], dict):
            data = detail_data["data"]
            data_fields = ["mail_uuid", "subject", "content", "sender_email", "status"]
            for field in data_fields:
                if field in data:
                    print(f"✅ data.{field} 필드 존재: {data[field]}")
                else:
                    print(f"❌ data.{field} 필드 누락")
        
        print("\n🎉 임시보관함 메일 상세 조회 API 수정이 성공적으로 완료되었습니다!")
        print("📋 Terminal#1016-1020 오류가 해결되었습니다.")
        return True
        
    elif detail_response.status_code == 403:
        print("❌ 여전히 403 Access Denied 오류 발생")
        print(f"응답 내용: {detail_response.text}")
        return False
        
    elif detail_response.status_code == 404:
        print("❌ 404 Not Found 오류 발생")
        print(f"응답 내용: {detail_response.text}")
        print("💡 조직 분리로 인한 정상적인 보안 동작일 수 있습니다.")
        return False
        
    else:
        print(f"❌ 예상치 못한 오류 발생: {detail_response.status_code}")
        print(f"응답 내용: {detail_response.text}")
        return False

if __name__ == "__main__":
    success = test_draft_mail_detail_with_existing_mail()
    if success:
        print("\n✅ 모든 테스트 통과!")
    else:
        print("\n❌ 테스트 실패!")