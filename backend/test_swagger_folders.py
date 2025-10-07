#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
스웨거 문서에서 INBOX 폴더 표시 확인 테스트
"""

import requests
import json

# 서버 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def test_swagger_folders():
    """스웨거 문서에서 메일 폴더 API 응답 스키마 확인"""
    print("📚 스웨거 문서 메일 폴더 API 테스트")
    print("=" * 60)

    # 1. 로그인
    print("🔐 관리자 로그인 중...")
    login_data = {
        "user_id": "admin01",
        "password": "test"
    }

    login_response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/login", json=login_data)
    print(f"로그인 상태: {login_response.status_code}")

    if login_response.status_code == 200:
        login_result = login_response.json()
        access_token = login_result["access_token"]
        print("✅ 로그인 성공")
        
        # 2. 메일 폴더 목록 조회 (새로운 응답 스키마 적용)
        print("\n📁 메일 폴더 목록 조회 중...")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Organization-ID": "3856a8c1-84a4-4019-9133-655cacab4bc9"
        }
        
        folders_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/mail/folders",
            headers=headers
        )
        
        print(f"폴더 목록 조회 상태: {folders_response.status_code}")
        
        if folders_response.status_code == 200:
            folders_result = folders_response.json()
            print("✅ 폴더 목록 조회 성공!")
            print(f"📊 응답 구조: {json.dumps(folders_result, indent=2, ensure_ascii=False)}")
            
            # INBOX 폴더 확인
            folders = folders_result.get('folders', [])
            inbox_found = False
            
            for folder in folders:
                if folder.get('name') == 'INBOX':
                    inbox_found = True
                    print(f"\n✅ INBOX 폴더 발견!")
                    print(f"   - 폴더 UUID: {folder.get('folder_uuid')}")
                    print(f"   - 폴더 타입: {folder.get('folder_type')}")
                    print(f"   - 메일 수: {folder.get('mail_count')}")
                    print(f"   - 시스템 폴더: {folder.get('is_system')}")
                    break
            
            if not inbox_found:
                print("❌ INBOX 폴더를 찾을 수 없습니다!")
                
            print(f"\n📂 전체 폴더 목록 ({len(folders)}개):")
            for i, folder in enumerate(folders, 1):
                print(f"   {i}. {folder.get('name')} ({folder.get('folder_type')})")
                print(f"      UUID: {folder.get('folder_uuid')}")
                print(f"      메일 수: {folder.get('mail_count')}")
                print(f"      시스템 폴더: {folder.get('is_system')}")
                print()
                
        else:
            print(f"❌ 폴더 목록 조회 실패: {folders_response.text}")
            
        # 3. 스웨거 OpenAPI 스키마 확인
        print("\n📖 OpenAPI 스키마 확인 중...")
        openapi_response = requests.get(f"{BASE_URL}/openapi.json")
        
        if openapi_response.status_code == 200:
            openapi_data = openapi_response.json()
            
            # 메일 폴더 API 스키마 확인
            paths = openapi_data.get('paths', {})
            folder_api = paths.get('/api/v1/mail/folders', {})
            get_method = folder_api.get('get', {})
            responses = get_method.get('responses', {})
            success_response = responses.get('200', {})
            content = success_response.get('content', {})
            json_content = content.get('application/json', {})
            schema = json_content.get('schema', {})
            
            print(f"✅ OpenAPI 스키마 확인 완료")
            print(f"📋 응답 스키마: {json.dumps(schema, indent=2, ensure_ascii=False)}")
            
            # FolderListResponse 스키마 확인
            if '$ref' in schema:
                ref_path = schema['$ref']
                print(f"📎 스키마 참조: {ref_path}")
                
                # 컴포넌트에서 실제 스키마 찾기
                components = openapi_data.get('components', {})
                schemas = components.get('schemas', {})
                
                if 'FolderListResponse' in schemas:
                    folder_list_schema = schemas['FolderListResponse']
                    print(f"📋 FolderListResponse 스키마:")
                    print(f"{json.dumps(folder_list_schema, indent=2, ensure_ascii=False)}")
                else:
                    print("❌ FolderListResponse 스키마를 찾을 수 없습니다!")
            
        else:
            print(f"❌ OpenAPI 스키마 조회 실패: {openapi_response.status_code}")
            
    else:
        print(f"❌ 로그인 실패: {login_response.text}")

    print("\n🔍 스웨거 문서 테스트 완료!")

if __name__ == "__main__":
    test_swagger_folders()