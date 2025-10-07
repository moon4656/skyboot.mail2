#!/usr/bin/env python3
"""
임시보관함 메일 상세 조회 API 수정 검증 테스트
Terminal#1016-1020 오류 해결 확인
"""

import requests
import json
from datetime import datetime

# API 기본 설정
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_draft_mail_detail_fix():
    """임시보관함 메일 상세 조회 API 수정 검증"""
    print("🧪 임시보관함 메일 상세 조회 API 수정 검증 테스트 시작")
    print("📋 Terminal#1016-1020 오류 해결 확인")
    
    # 1. 로그인
    print("\n1️⃣ 사용자 로그인")
    login_data = {
        "user_id": "user01",
        "password": "test"
    }
    
    login_response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    print(f"로그인 응답 상태: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"❌ 로그인 실패: {login_response.text}")
        return False
    
    login_result = login_response.json()
    access_token = login_result["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    print("✅ 로그인 성공")
    
    # 2. 임시보관함 조회하여 메일 UUID 가져오기
    print("\n2️⃣ 임시보관함 조회")
    drafts_response = requests.get(f"{API_BASE}/mail/drafts", headers=headers)
    print(f"임시보관함 조회 상태: {drafts_response.status_code}")
    
    if drafts_response.status_code != 200:
        print(f"❌ 임시보관함 조회 실패: {drafts_response.text}")
        return False
    
    drafts_data = drafts_response.json()
    print(f"임시보관함 응답: {json.dumps(drafts_data, indent=2, ensure_ascii=False)}")
    
    # 임시보관함에 메일이 있는지 확인
    if not drafts_data.get("items") or len(drafts_data["items"]) == 0:
        print("📭 임시보관함이 비어있습니다.")
        
        # 3. 임시보관함 메일 생성 (테스트용) - Form 데이터로 전송
        print("\n3️⃣ 테스트용 임시보관함 메일 생성")
        draft_mail_data = {
            "to_emails": "test@example.com",
            "subject": "임시보관함 테스트 메일",
            "content": "이 메일은 임시보관함 상세 조회 테스트를 위한 메일입니다.",
            "priority": "normal"
        }
        
        send_response = requests.post(f"{API_BASE}/mail/send", data=draft_mail_data, headers=headers)
        print(f"임시보관함 메일 생성 상태: {send_response.status_code}")
        
        if send_response.status_code != 200:
            print(f"❌ 임시보관함 메일 생성 실패: {send_response.text}")
            return False
        
        # 다시 임시보관함 조회
        drafts_response = requests.get(f"{API_BASE}/mail/drafts", headers=headers)
        drafts_data = drafts_response.json()
    
    # 첫 번째 임시보관함 메일의 UUID 가져오기
    if drafts_data.get("items") and len(drafts_data["items"]) > 0:
        first_draft = drafts_data["items"][0]
        mail_uuid = first_draft["mail_uuid"]
        print(f"📧 테스트할 임시보관함 메일 UUID: {mail_uuid}")
        
        # 4. 임시보관함 메일 상세 조회 (수정된 API 테스트)
        print("\n4️⃣ 임시보관함 메일 상세 조회 (수정된 API)")
        detail_response = requests.get(f"{API_BASE}/mail/drafts/{mail_uuid}", headers=headers)
        print(f"임시보관함 메일 상세 조회 상태: {detail_response.status_code}")
        print(f"응답 헤더: {dict(detail_response.headers)}")
        
        if detail_response.status_code == 200:
            print("✅ 임시보관함 메일 상세 조회 성공!")
            detail_data = detail_response.json()
            print(f"상세 정보: {json.dumps(detail_data, indent=2, ensure_ascii=False, default=str)}")
            
            # 5. 응답 구조 검증
            print("\n5️⃣ 응답 구조 검증")
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
                        print(f"✅ data.{field} 필드 존재")
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
            print("❌ 404 Not Found 오류 발생 (조직 분리로 인한 정상적인 보안 동작일 수 있음)")
            print(f"응답 내용: {detail_response.text}")
            return False
            
        else:
            print(f"❌ 예상치 못한 오류 발생: {detail_response.status_code}")
            print(f"응답 내용: {detail_response.text}")
            return False
    else:
        print("❌ 임시보관함에 테스트할 메일이 없습니다.")
        return False

if __name__ == "__main__":
    success = test_draft_mail_detail_fix()
    if success:
        print("\n✅ 모든 테스트 통과!")
    else:
        print("\n❌ 테스트 실패!")