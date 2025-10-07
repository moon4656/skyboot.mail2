#!/usr/bin/env python3
"""
Swagger UI 접근성 확인 및 메일 상태 필터 검증
"""

import requests
import json
from datetime import datetime

# 설정
BASE_URL = "http://localhost:8000"

def test_swagger_access():
    """Swagger UI 접근성 테스트"""
    print("📚 Swagger UI 접근성 테스트 시작")
    print(f"⏰ 테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. Swagger UI 페이지 접근
    print("\n🌐 Swagger UI 페이지 접근 중...")
    try:
        swagger_response = requests.get(f"{BASE_URL}/docs", timeout=10)
        print(f"Swagger UI 상태: {swagger_response.status_code}")
        
        if swagger_response.status_code == 200:
            print("✅ Swagger UI 접근 성공!")
            print(f"🔗 Swagger URL: {BASE_URL}/docs")
            
            # HTML 내용 확인
            content = swagger_response.text
            if "swagger" in content.lower() or "openapi" in content.lower():
                print("✅ Swagger UI 페이지가 정상적으로 로드됨")
            else:
                print("⚠️ Swagger UI 페이지 내용이 예상과 다름")
        else:
            print(f"❌ Swagger UI 접근 실패: {swagger_response.status_code}")
            print(f"응답 내용: {swagger_response.text[:200]}...")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Swagger UI 접근 중 오류: {str(e)}")
    
    # 2. OpenAPI 스키마 조회
    print("\n📋 OpenAPI 스키마 조회 중...")
    try:
        openapi_response = requests.get(f"{BASE_URL}/openapi.json", timeout=10)
        print(f"OpenAPI 스키마 상태: {openapi_response.status_code}")
        
        if openapi_response.status_code == 200:
            print("✅ OpenAPI 스키마 조회 성공!")
            
            openapi_data = openapi_response.json()
            
            # API 엔드포인트 수 확인
            paths = openapi_data.get("paths", {})
            print(f"📊 총 API 엔드포인트 수: {len(paths)}")
            
            # 메일 관련 엔드포인트 확인
            mail_endpoints = [path for path in paths.keys() if "/mail/" in path]
            print(f"📧 메일 관련 엔드포인트 수: {len(mail_endpoints)}")
            
            # 휴지통 API 확인
            trash_endpoint = "/api/v1/mail/trash"
            if trash_endpoint in paths:
                print(f"✅ 휴지통 API 엔드포인트 확인: {trash_endpoint}")
                
                # 휴지통 API의 파라미터 확인
                trash_api = paths[trash_endpoint]
                if "get" in trash_api:
                    get_method = trash_api["get"]
                    parameters = get_method.get("parameters", [])
                    
                    print(f"📋 휴지통 API 파라미터:")
                    for param in parameters:
                        param_name = param.get("name", "N/A")
                        param_type = param.get("schema", {}).get("type", "N/A")
                        param_desc = param.get("description", "N/A")
                        print(f"   - {param_name} ({param_type}): {param_desc}")
                        
                        # status 파라미터의 enum 값 확인
                        if param_name == "status":
                            schema = param.get("schema", {})
                            if "$ref" in schema:
                                ref_path = schema["$ref"]
                                print(f"   📎 status 파라미터 참조: {ref_path}")
                            elif "enum" in schema:
                                enum_values = schema["enum"]
                                print(f"   📋 status 가능한 값: {enum_values}")
            else:
                print(f"❌ 휴지통 API 엔드포인트를 찾을 수 없음: {trash_endpoint}")
            
            # 스키마 정의에서 MailStatus enum 확인
            components = openapi_data.get("components", {})
            schemas = components.get("schemas", {})
            
            if "MailStatus" in schemas:
                mail_status_schema = schemas["MailStatus"]
                print(f"\n📋 MailStatus enum 정의:")
                print(f"   타입: {mail_status_schema.get('type', 'N/A')}")
                
                enum_values = mail_status_schema.get("enum", [])
                if enum_values:
                    print(f"   가능한 값: {enum_values}")
                else:
                    print("   ⚠️ enum 값을 찾을 수 없음")
            else:
                print("❌ MailStatus 스키마를 찾을 수 없음")
                
        else:
            print(f"❌ OpenAPI 스키마 조회 실패: {openapi_response.status_code}")
            print(f"응답 내용: {openapi_response.text[:200]}...")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ OpenAPI 스키마 조회 중 오류: {str(e)}")
    except json.JSONDecodeError as e:
        print(f"❌ OpenAPI 스키마 JSON 파싱 오류: {str(e)}")
    
    # 3. 서버 상태 확인
    print("\n🔍 서버 상태 확인 중...")
    try:
        health_response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"서버 루트 상태: {health_response.status_code}")
        
        if health_response.status_code == 200:
            print("✅ 서버가 정상적으로 응답함")
        else:
            print(f"⚠️ 서버 응답 상태가 비정상: {health_response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 서버 상태 확인 중 오류: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🏁 Swagger UI 접근성 테스트 완료!")
    print(f"⏰ 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    test_swagger_access()