#!/usr/bin/env python3
"""
parent_id 수정 테스트 스크립트
"""

import requests
import json

# API 설정
BASE_URL = "http://localhost:8001"
LOGIN_URL = f"{BASE_URL}/api/v1/auth/login"
FOLDER_URL = f"{BASE_URL}/api/v1/mail/folders"

def test_parent_id_fix():
    """parent_id 수정이 제대로 작동하는지 테스트"""
    
    print("🔧 parent_id 수정 테스트 시작")
    print("=" * 60)
    
    # 1. 로그인
    print("\n🔐 로그인 중...")
    login_data = {
        "user_id": "user01",
        "password": "test"
    }
    
    response = requests.post(LOGIN_URL, json=login_data)
    if response.status_code != 200:
        print(f"❌ 로그인 실패: {response.status_code}")
        print(f"응답: {response.text}")
        return
    
    token_data = response.json()
    access_token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print("✅ 로그인 성공")
    
    # 2. parent_id가 177인 폴더 생성 테스트
    print("\n📁 parent_id가 177인 폴더 생성 테스트...")
    folder_data = {
        "name": "parent_id 테스트 폴더",
        "folder_type": "custom",
        "parent_id": 177
    }
    
    response = requests.post(FOLDER_URL, json=folder_data, headers=headers)
    print(f"응답 상태: {response.status_code}")
    print(f"응답 내용: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        folder_id = result.get("id")
        print(f"✅ 폴더 생성 성공! 폴더 ID: {folder_id}")
        
        # 3. 데이터베이스에서 parent_id 확인
        print("\n🔍 데이터베이스에서 parent_id 확인...")
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from sqlalchemy import create_engine, text
        from app.config import settings
        
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, name, parent_id, created_at
                FROM mail_folders 
                WHERE name = 'parent_id 테스트 폴더'
                ORDER BY created_at DESC
                LIMIT 1
            """))
            
            folder = result.fetchone()
            if folder:
                print(f"  폴더 ID: {folder.id}")
                print(f"  폴더명: {folder.name}")
                print(f"  parent_id: {folder.parent_id}")
                print(f"  생성시간: {folder.created_at}")
                
                if folder.parent_id == 177:
                    print("🎉 parent_id가 올바르게 저장되었습니다!")
                else:
                    print(f"❌ parent_id가 잘못 저장됨: {folder.parent_id} (예상: 177)")
            else:
                print("❌ 생성된 폴더를 찾을 수 없습니다.")
    else:
        print(f"❌ 폴더 생성 실패: {response.status_code}")
    
    # 4. parent_id가 None인 폴더 생성 테스트
    print("\n📁 parent_id가 None인 폴더 생성 테스트...")
    folder_data = {
        "name": "최상위 테스트 폴더",
        "folder_type": "custom",
        "parent_id": None
    }
    
    response = requests.post(FOLDER_URL, json=folder_data, headers=headers)
    print(f"응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ 최상위 폴더 생성 성공!")
    else:
        print(f"❌ 최상위 폴더 생성 실패: {response.status_code}")
        print(f"응답: {response.text}")

if __name__ == "__main__":
    test_parent_id_fix()