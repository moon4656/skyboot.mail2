#!/usr/bin/env python3
"""
메일 발송 디버깅 테스트 스크립트
"""

import requests
import json
import time

def test_mail_sending_with_debug():
    """메일 발송 과정을 상세히 디버깅합니다."""
    
    base_url = "http://localhost:8000/api/v1"
    
    print("🔍 메일 발송 디버깅 테스트 시작...")
    
    try:
        # 1. 로그인
        print("\n1️⃣ 로그인 시도...")
        login_data = {
            "user_id": "testuser_folder",
            "password": "testpass123"
        }
        
        login_response = requests.post(f"{base_url}/auth/login", json=login_data)
        print(f"로그인 응답 상태: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"❌ 로그인 실패: {login_response.text}")
            return False
            
        login_result = login_response.json()
        access_token = login_result["access_token"]
        print("✅ 로그인 성공!")
        
        # 2. 헤더 설정
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # 3. 메일 발송 데이터 준비
        print("\n2️⃣ 메일 발송 데이터 준비...")
        mail_data = {
            "to": ["debug_test@example.com"],
            "subject": "디버깅 테스트 메일",
            "body_text": "이것은 메일 발송 디버깅을 위한 테스트 메일입니다.",
            "priority": "normal"
        }
        
        print(f"메일 데이터: {json.dumps(mail_data, ensure_ascii=False, indent=2)}")
        
        # 4. 메일 발송 요청
        print("\n3️⃣ 메일 발송 요청...")
        print(f"요청 URL: {base_url}/mail/send-json")
        print(f"요청 헤더: {headers}")
        
        mail_response = requests.post(
            f"{base_url}/mail/send-json",
            json=mail_data,
            headers=headers,
            timeout=30  # 30초 타임아웃
        )
        
        print(f"메일 발송 응답 상태: {mail_response.status_code}")
        print(f"메일 발송 응답 헤더: {dict(mail_response.headers)}")
        print(f"메일 발송 응답 본문: {mail_response.text}")
        
        if mail_response.status_code == 200:
            mail_result = mail_response.json()
            print("✅ 메일 발송 API 호출 성공!")
            print(f"응답 데이터: {json.dumps(mail_result, ensure_ascii=False, indent=2)}")
            
            # 메일 UUID 추출
            mail_uuid = mail_result.get("mail_uuid")
            if mail_uuid:
                print(f"📧 메일 UUID: {mail_uuid}")
                
                # 5. 잠시 대기 후 메일 상태 확인
                print("\n4️⃣ 메일 상태 확인...")
                time.sleep(2)
                
                # 데이터베이스에서 메일 확인
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                
                from app.database.mail import get_db
                from app.model.mail_model import Mail, MailInFolder
                
                db = next(get_db())
                try:
                    # 메일 존재 확인
                    mail = db.query(Mail).filter(Mail.mail_uuid == mail_uuid).first()
                    if mail:
                        print(f"✅ 메일이 데이터베이스에 저장됨: {mail.mail_uuid}")
                        print(f"   - 상태: {mail.status}")
                        print(f"   - 제목: {mail.subject}")
                        print(f"   - 발송 시간: {mail.sent_at}")
                        
                        # 폴더 할당 확인
                        folder_assignments = db.query(MailInFolder).filter(
                            MailInFolder.mail_uuid == mail_uuid
                        ).all()
                        
                        print(f"📁 폴더 할당 수: {len(folder_assignments)}")
                        for assignment in folder_assignments:
                            print(f"   - 폴더 UUID: {assignment.folder_uuid}")
                            print(f"   - 사용자 UUID: {assignment.user_uuid}")
                        
                    else:
                        print(f"❌ 메일이 데이터베이스에 없음: {mail_uuid}")
                        
                finally:
                    db.close()
                    
            return True
        else:
            print(f"❌ 메일 발송 실패: {mail_response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 요청 타임아웃 발생")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 서버 연결 실패")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_mail_sending_with_debug()
    if success:
        print("\n🎉 메일 발송 디버깅 테스트 완료!")
    else:
        print("\n💥 메일 발송 디버깅 테스트 실패!")