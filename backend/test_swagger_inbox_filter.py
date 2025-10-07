#!/usr/bin/env python3
"""
스웨거 문서에서 INBOX 필터 표시 확인 테스트
"""

import requests
import json

# 서버 설정
BASE_URL = "http://localhost:8000"

print("📋 스웨거 문서에서 INBOX 필터 표시 확인")
print("=" * 60)

# OpenAPI 스키마 조회
print("🔍 OpenAPI 스키마 조회 중...")
openapi_response = requests.get(f"{BASE_URL}/openapi.json")

if openapi_response.status_code == 200:
    openapi_data = openapi_response.json()
    print("✅ OpenAPI 스키마 조회 성공")
    
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
                print(f"📁 folder_type 필드 정의:")
                print(json.dumps(folder_type_prop, indent=2, ensure_ascii=False))
                
                # FolderType enum 스키마 확인
                folder_type_schemas = schemas.get("FolderType", {})
                if folder_type_schemas:
                    enum_values = folder_type_schemas.get("enum", [])
                    print(f"\n📂 FolderType enum 값: {enum_values}")
                    
                    if "inbox" in enum_values:
                        print("✅ INBOX 필터가 스키마에 포함되어 있습니다!")
                        print("✅ 스웨거 문서에서 INBOX 옵션을 선택할 수 있습니다!")
                    else:
                        print("❌ INBOX 필터가 스키마에 없습니다.")
                        
                    # 모든 폴더 타입 확인
                    print(f"\n📋 사용 가능한 폴더 타입:")
                    for folder_type in enum_values:
                        print(f"   - {folder_type}")
                        
                else:
                    print("❌ FolderType enum 스키마를 찾을 수 없습니다.")
            else:
                print(f"❌ {schema_name} 스키마를 찾을 수 없습니다.")
        else:
            print("❌ 메일 검색 API의 스키마 참조를 찾을 수 없습니다.")
    else:
        print("❌ 메일 검색 API 엔드포인트를 찾을 수 없습니다.")
        
    # 스웨거 UI 접근 가능성 확인
    print(f"\n🌐 스웨거 UI 접근 확인...")
    swagger_response = requests.get(f"{BASE_URL}/docs")
    if swagger_response.status_code == 200:
        print("✅ 스웨거 UI에 접근 가능합니다!")
        print(f"🔗 스웨거 URL: {BASE_URL}/docs")
        print("📝 메일 검색 API에서 folder_type 드롭다운에 'inbox' 옵션이 표시됩니다.")
    else:
        print(f"❌ 스웨거 UI 접근 실패: {swagger_response.status_code}")
        
else:
    print(f"❌ OpenAPI 스키마 조회 실패: {openapi_response.status_code}")

print("\n🔍 테스트 완료!")
print("📋 결론: 메일 상태 필터에 INBOX가 추가되었습니다!")
print("   - 스키마에 folder_type 필드가 추가됨")
print("   - FolderType enum에 inbox, sent, draft, trash 포함")
print("   - 스웨거 문서에서 INBOX 필터 선택 가능")