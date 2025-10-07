#!/usr/bin/env python3
"""
메일 검색 API에서 INBOX 폴더 타입 필터 테스트
"""

import requests
import json

# 서버 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

print("📬 메일 검색 API INBOX 필터 테스트")
print("=" * 60)

# 1. 로그인
print("🔐 관리자 로그인 중...")
login_data = {
    "user_id": "admin01",
    "password": "test"
}

login_response = requests.post(
    f"{BASE_URL}{API_PREFIX}/auth/login", 
    json=login_data,
    headers={"Content-Type": "application/json"}
)
print(f"로그인 상태: {login_response.status_code}")

if login_response.status_code == 200:
    login_result = login_response.json()
    access_token = login_result["access_token"]
    print("✅ 로그인 성공")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Organization-ID": "3856a8c1-84a4-4019-9133-655cacab4bc9",
        "Content-Type": "application/json"
    }
    
    # 2. 메일 검색 API 스키마 확인 (OpenAPI)
    print("\n📋 OpenAPI 스키마에서 메일 검색 API 확인 중...")
    openapi_response = requests.get(f"{BASE_URL}/openapi.json")
    
    if openapi_response.status_code == 200:
        openapi_data = openapi_response.json()
        
        # 메일 검색 API 스키마 확인
        search_endpoint = openapi_data.get("paths", {}).get("/api/v1/mail/search", {})
        if search_endpoint:
            post_method = search_endpoint.get("post", {})
            request_body = post_method.get("requestBody", {})
            content = request_body.get("content", {})
            json_content = content.get("application/json", {})
            schema_ref = json_content.get("schema", {}).get("$ref", "")
            
            if schema_ref:
                # 스키마 참조에서 실제 스키마 찾기
                schema_name = schema_ref.split("/")[-1]  # MailSearchRequest
                schemas = openapi_data.get("components", {}).get("schemas", {})
                mail_search_schema = schemas.get(schema_name, {})
                
                if mail_search_schema:
                    properties = mail_search_schema.get("properties", {})
                    folder_type_prop = properties.get("folder_type", {})
                    
                    print(f"✅ {schema_name} 스키마 발견")
                    print(f"📁 folder_type 필드: {folder_type_prop}")
                    
                    # folder_type enum 값 확인
                    if "allOf" in folder_type_prop:
                        enum_ref = folder_type_prop["allOf"][0].get("$ref", "")
                        if enum_ref:
                            enum_name = enum_ref.split("/")[-1]  # FolderType
                            folder_type_enum = schemas.get(enum_name, {})
                            enum_values = folder_type_enum.get("enum", [])
                            print(f"📂 FolderType enum 값: {enum_values}")
                            
                            if "inbox" in enum_values:
                                print("✅ INBOX 필터가 스키마에 포함되어 있습니다!")
                            else:
                                print("❌ INBOX 필터가 스키마에 없습니다.")
                    else:
                        print("⚠️ folder_type 필드의 enum 참조를 찾을 수 없습니다.")
                else:
                    print(f"❌ {schema_name} 스키마를 찾을 수 없습니다.")
            else:
                print("❌ 메일 검색 API의 스키마 참조를 찾을 수 없습니다.")
        else:
            print("❌ 메일 검색 API 엔드포인트를 찾을 수 없습니다.")
    else:
        print(f"❌ OpenAPI 스키마 조회 실패: {openapi_response.status_code}")
    
    # 3. 실제 메일 검색 API 테스트 (INBOX 필터)
    print("\n🔍 INBOX 필터로 메일 검색 테스트...")
    search_data = {
        "folder_type": "inbox",
        "page": 1,
        "limit": 10
    }
    
    search_response = requests.post(
        f"{BASE_URL}{API_PREFIX}/mail/search",
        headers=headers,
        json=search_data
    )
    
    print(f"INBOX 필터 검색 상태: {search_response.status_code}")
    
    if search_response.status_code == 200:
        search_result = search_response.json()
        print("✅ INBOX 필터 검색 성공!")
        print(f"📊 검색 결과: {search_result.get('total', 0)}개")
        
        mails = search_result.get('mails', [])
        if mails:
            print(f"\n📧 INBOX 메일 목록 ({len(mails)}개):")
            for i, mail in enumerate(mails[:3], 1):
                print(f"   {i}. 제목: {mail.get('subject', 'N/A')}")
                print(f"      상태: {mail.get('status', 'N/A')}")
                print(f"      발송자: {mail.get('sender', {}).get('email', 'N/A')}")
                print()
        else:
            print("📭 INBOX에 메일이 없습니다.")
    else:
        print(f"❌ INBOX 필터 검색 실패: {search_response.text}")
    
    # 4. 다른 폴더 타입들도 테스트
    folder_types = ["sent", "draft", "trash"]
    for folder_type in folder_types:
        print(f"\n🔍 {folder_type.upper()} 필터로 메일 검색 테스트...")
        search_data = {
            "folder_type": folder_type,
            "page": 1,
            "limit": 5
        }
        
        search_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/mail/search",
            headers=headers,
            json=search_data
        )
        
        if search_response.status_code == 200:
            search_result = search_response.json()
            total = search_result.get('total', 0)
            print(f"✅ {folder_type.upper()} 필터 검색 성공! 결과: {total}개")
        else:
            print(f"❌ {folder_type.upper()} 필터 검색 실패: {search_response.status_code}")

else:
    print(f"❌ 로그인 실패: {login_response.text}")

print("\n🔍 테스트 완료!")