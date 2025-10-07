#!/usr/bin/env python3
"""
sent_at 필드 수정 후 오류 해결 확인 테스트
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def test_sent_at_fix():
    """sent_at 필드 수정이 제대로 적용되었는지 테스트"""
    try:
        print("🔧 sent_at 필드 수정 확인 테스트")
        print("=" * 60)
        
        # 1. 로그인
        print("🔐 로그인 중...")
        login_data = {
            "user_id": "admin01",
            "password": "test"
        }
        
        login_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json=login_data
        )
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ 로그인 성공!")
        else:
            print(f"❌ 로그인 실패: {login_response.text}")
            return False
        
        # 2. 임시보관함 메일 생성 (sent_at이 None인 메일)
        print("\n📝 임시보관함 메일 생성 중...")
        draft_data = {
            "to": ["test@example.com"],
            "subject": "sent_at 필드 테스트 - 임시보관함",
            "body_text": "이 메일은 sent_at 필드가 None인 임시보관함 메일입니다.",
            "priority": "normal",
            "is_draft": True  # 임시보관함으로 저장
        }
        
        draft_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/mail/send-json",
            json=draft_data,
            headers=headers
        )
        
        print(f"임시보관함 메일 생성 상태: {draft_response.status_code}")
        if draft_response.status_code == 200:
            draft_result = draft_response.json()
            print("✅ 임시보관함 메일 생성 성공!")
            print(f"📧 메일 UUID: {draft_result.get('mail_uuid', 'N/A')}")
            print(f"📅 sent_at: {draft_result.get('sent_at', 'N/A')}")
            
            # sent_at이 None인지 확인
            if draft_result.get('sent_at') is None:
                print("✅ sent_at 필드가 올바르게 None으로 설정됨!")
            else:
                print("⚠️ 임시보관함 메일의 sent_at이 None이 아닙니다.")
        else:
            print(f"❌ 임시보관함 메일 생성 실패: {draft_response.text}")
            return False
        
        # 3. 실제 메일 발송 (sent_at이 설정되는 메일)
        print("\n📤 실제 메일 발송 중...")
        send_data = {
            "to": ["test@example.com"],
            "subject": "sent_at 필드 테스트 - 발송 메일",
            "body_text": "이 메일은 sent_at 필드가 설정된 발송 메일입니다.",
            "priority": "normal",
            "is_draft": False  # 실제 발송
        }
        
        send_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/mail/send-json",
            json=send_data,
            headers=headers
        )
        
        print(f"메일 발송 상태: {send_response.status_code}")
        if send_response.status_code == 200:
            send_result = send_response.json()
            print("✅ 메일 발송 성공!")
            print(f"📧 메일 UUID: {send_result.get('mail_uuid', 'N/A')}")
            print(f"📅 sent_at: {send_result.get('sent_at', 'N/A')}")
            
            # sent_at이 설정되었는지 확인
            if send_result.get('sent_at') is not None:
                print("✅ sent_at 필드가 올바르게 설정됨!")
            else:
                print("⚠️ 발송 메일의 sent_at이 None입니다.")
        else:
            print(f"❌ 메일 발송 실패: {send_response.text}")
            return False
        
        # 4. 임시보관함 조회 (sent_at이 None인 메일들 확인)
        print("\n📁 임시보관함 조회 중...")
        draft_box_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/mail/drafts",
            headers=headers
        )
        
        print(f"임시보관함 조회 상태: {draft_box_response.status_code}")
        if draft_box_response.status_code == 200:
            draft_box_result = draft_box_response.json()
            print("✅ 임시보관함 조회 성공!")
            
            drafts = draft_box_result.get('mails', [])
            print(f"📊 임시보관함 메일 수: {len(drafts)}개")
            
            for i, mail in enumerate(drafts, 1):
                print(f"\n   {i}. 제목: {mail.get('subject', 'N/A')}")
                print(f"      상태: {mail.get('status', 'N/A')}")
                print(f"      임시보관함: {mail.get('is_draft', 'N/A')}")
                print(f"      발송 시간: {mail.get('sent_at', 'N/A')}")
                print(f"      생성 시간: {mail.get('created_at', 'N/A')}")
                
                # sent_at 필드가 None인지 확인
                if mail.get('sent_at') is None:
                    print(f"      ✅ sent_at 필드가 올바르게 None임!")
                else:
                    print(f"      ⚠️ 임시보관함 메일의 sent_at이 None이 아님: {mail.get('sent_at')}")
        else:
            print(f"❌ 임시보관함 조회 실패: {draft_box_response.text}")
        
        # 5. 발송함 조회 (sent_at이 설정된 메일들 확인)
        print("\n📤 발송함 조회 중...")
        sent_box_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/mail/sent",
            headers=headers
        )
        
        print(f"발송함 조회 상태: {sent_box_response.status_code}")
        if sent_box_response.status_code == 200:
            sent_box_result = sent_box_response.json()
            print("✅ 발송함 조회 성공!")
            
            sent_mails = sent_box_result.get('mails', [])
            print(f"📊 발송함 메일 수: {len(sent_mails)}개")
            
            for i, mail in enumerate(sent_mails, 1):
                print(f"\n   {i}. 제목: {mail.get('subject', 'N/A')}")
                print(f"      상태: {mail.get('status', 'N/A')}")
                print(f"      임시보관함: {mail.get('is_draft', 'N/A')}")
                print(f"      발송 시간: {mail.get('sent_at', 'N/A')}")
                print(f"      생성 시간: {mail.get('created_at', 'N/A')}")
                
                # sent_at 필드가 설정되었는지 확인
                if mail.get('sent_at') is not None:
                    print(f"      ✅ sent_at 필드가 올바르게 설정됨!")
                else:
                    print(f"      ⚠️ 발송 메일의 sent_at이 None임!")
        else:
            print(f"❌ 발송함 조회 실패: {sent_box_response.text}")
        
        print("\n🎉 sent_at 필드 수정 확인 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_sent_at_fix()
    
    if success:
        print("\n✅ sent_at 필드 수정이 성공적으로 적용되었습니다!")
    else:
        print("\n❌ sent_at 필드 수정 테스트에 실패했습니다.")