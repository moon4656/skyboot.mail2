#!/usr/bin/env python3
"""
MailInFolder org_id 오류 수정 테스트 스크립트
"""

import requests
import json
from sqlalchemy import create_engine, text
from app.config import settings

# API 설정
BASE_URL = "http://localhost:8001"
LOGIN_URL = f"{BASE_URL}/api/v1/auth/login"

def main():
    print("🔧 MailInFolder org_id 오류 수정 테스트 시작")
    print("=" * 60)
    
    try:
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
        
        login_result = response.json()
        print(f"로그인 응답: {json.dumps(login_result, indent=2, ensure_ascii=False)}")
        
        # 토큰 추출 (응답 구조에 따라 조정)
        if "data" in login_result and "access_token" in login_result["data"]:
            token = login_result["data"]["access_token"]
        elif "access_token" in login_result:
            token = login_result["access_token"]
        else:
            print("❌ 토큰을 찾을 수 없습니다.")
            return
            
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ 로그인 성공")
        
        # 2. 데이터베이스에서 테스트용 메일과 폴더 조회
        print("\n🔍 테스트용 메일과 폴더 조회...")
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # 최근 메일 조회
            mail_result = conn.execute(text("""
                SELECT mail_uuid, subject, sender_uuid 
                FROM mails 
                WHERE org_id = '3856a8c1-84a4-4019-9133-655cacab4bc9'
                ORDER BY created_at DESC 
                LIMIT 1
            """)).fetchone()
            
            if not mail_result:
                print("❌ 테스트용 메일을 찾을 수 없습니다.")
                return
            
            mail_uuid = mail_result.mail_uuid
            print(f"📧 테스트 메일: {mail_uuid} - {mail_result.subject}")
            
            # 사용자 폴더 조회
            folder_result = conn.execute(text("""
                SELECT folder_uuid, name, folder_type 
                FROM mail_folders 
                WHERE user_uuid = (
                    SELECT user_uuid FROM mail_users 
                    WHERE email = 'user01@example.com' 
                    AND org_id = '3856a8c1-84a4-4019-9133-655cacab4bc9'
                )
                AND folder_type = 'custom'
                ORDER BY created_at DESC 
                LIMIT 1
            """)).fetchone()
            
            if not folder_result:
                print("❌ 테스트용 폴더를 찾을 수 없습니다.")
                return
            
            folder_uuid = folder_result.folder_uuid
            print(f"📁 테스트 폴더: {folder_uuid} - {folder_result.name}")
        
        # 3. 메일을 폴더로 이동 테스트
        print(f"\n📁 메일을 폴더로 이동 테스트...")
        move_url = f"{BASE_URL}/api/v1/mail/folders/{folder_uuid}/mails/{mail_uuid}"
        
        response = requests.post(move_url, headers=headers)
        print(f"응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 메일 이동 성공!")
            print(f"응답: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 4. 데이터베이스에서 이동 결과 확인
            print(f"\n🔍 데이터베이스에서 이동 결과 확인...")
            with engine.connect() as conn:
                check_result = conn.execute(text("""
                    SELECT mif.mail_uuid, mif.folder_uuid, mf.name as folder_name, mif.is_read
                    FROM mail_in_folders mif
                    JOIN mail_folders mf ON mif.folder_uuid = mf.folder_uuid
                    WHERE mif.mail_uuid = :mail_uuid
                """), {"mail_uuid": mail_uuid}).fetchone()
                
                if check_result:
                    print(f"  메일 UUID: {check_result.mail_uuid}")
                    print(f"  폴더 UUID: {check_result.folder_uuid}")
                    print(f"  폴더명: {check_result.folder_name}")
                    print(f"  읽음 상태: {check_result.is_read}")
                    print("🎉 메일이 올바르게 폴더에 할당되었습니다!")
                else:
                    print("❌ 메일-폴더 관계를 찾을 수 없습니다.")
        else:
            print(f"❌ 메일 이동 실패: {response.status_code}")
            print(f"응답: {response.text}")
            
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()