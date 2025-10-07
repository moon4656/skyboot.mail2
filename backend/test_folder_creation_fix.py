#!/usr/bin/env python3
"""
폴더 생성 API 수정 사항 테스트 스크립트
"""

import requests
import json
import sys

def test_folder_creation():
    """폴더 생성 API 테스트"""
    base_url = "http://localhost:8001/api/v1"
    
    # 1. 로그인하여 토큰 받기
    print("1. 로그인 중...")
    login_data = {
        "user_id": "user01",
        "password": "test"
    }
    
    try:
        login_response = requests.post(
            f"{base_url}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code != 200:
            print(f"로그인 실패: {login_response.status_code}")
            print(f"응답: {login_response.text}")
            return False
            
        login_result = login_response.json()
        access_token = login_result.get("access_token")
        
        if not access_token:
            print("액세스 토큰을 받지 못했습니다.")
            return False
            
        print("✅ 로그인 성공")
        
    except Exception as e:
        print(f"로그인 중 오류 발생: {e}")
        return False
    
    # 2. 폴더 생성 테스트
    print("\n2. 폴더 생성 테스트...")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    folder_data = {
        "name": "테스트 폴더 수정됨",
        "folder_type": "custom"
    }
    
    try:
        folder_response = requests.post(
            f"{base_url}/mail/folders",
            json=folder_data,
            headers=headers
        )
        
        print(f"폴더 생성 응답 상태: {folder_response.status_code}")
        print(f"폴더 생성 응답: {folder_response.text}")
        
        if folder_response.status_code == 200:
            print("✅ 폴더 생성 성공!")
            folder_result = folder_response.json()
            folder_uuid = folder_result.get("folder_uuid")
            
            # 3. 폴더 수정 테스트
            if folder_uuid:
                print(f"\n3. 폴더 수정 테스트 (UUID: {folder_uuid})...")
                update_data = {
                    "name": "수정된 폴더명"
                }
                
                update_response = requests.put(
                    f"{base_url}/mail/folders/{folder_uuid}",
                    json=update_data,
                    headers=headers
                )
                
                print(f"폴더 수정 응답 상태: {update_response.status_code}")
                print(f"폴더 수정 응답: {update_response.text}")
                
                if update_response.status_code == 200:
                    print("✅ 폴더 수정 성공!")
                else:
                    print("❌ 폴더 수정 실패")
            
            return True
        else:
            print("❌ 폴더 생성 실패")
            return False
            
    except Exception as e:
        print(f"폴더 생성 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    print("=== 폴더 생성 API 수정 사항 테스트 ===")
    success = test_folder_creation()
    
    if success:
        print("\n🎉 모든 테스트 통과!")
        sys.exit(0)
    else:
        print("\n💥 테스트 실패")
        sys.exit(1)