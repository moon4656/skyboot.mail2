#!/usr/bin/env python3
"""
수정된 메일 폴더 자동 할당 로직 테스트 스크립트

이 스크립트는 다음 기능들을 테스트합니다:
1. 메일 발송 시 보낸편지함 자동 할당
2. 메일 수신 시 받은편지함 자동 할당  
3. 임시저장 메일의 임시보관함 자동 할당
"""

import sys
import os
import requests
import json
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# API 기본 URL
BASE_URL = "http://localhost:8000"

def get_auth_token(email: str, password: str) -> str:
    """사용자 인증 토큰을 가져옵니다."""
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"로그인 실패: {response.status_code} - {response.text}")

def test_send_mail_folder_assignment():
    """메일 발송 시 폴더 자동 할당 테스트"""
    
    print("📤 메일 발송 시 폴더 자동 할당 테스트 시작...")
    
    try:
        # 발신자 로그인
        sender_token = get_auth_token("testuser2@example.com", "testpassword123")
        
        # 메일 발송 데이터 (Form 형식)
        mail_data = {
            "to_emails": "testuser1@example.com",
            "subject": f"폴더 할당 테스트 메일 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "content": "이 메일은 폴더 자동 할당 로직을 테스트하기 위한 메일입니다.",
            "priority": "normal"
        }
        
        headers = {
            "Authorization": f"Bearer {sender_token}"
        }
        
        # 메일 발송 (Form 데이터로 전송)
        send_response = requests.post(
            f"{BASE_URL}/mail/send",
            headers=headers,
            data=mail_data
        )
        
        if send_response.status_code == 200:
            result = send_response.json()
            mail_uuid = result.get("mail_uuid")
            print(f"   ✅ 메일 발송 성공: mail_uuid={mail_uuid}")
            
            # 발신자의 보낸편지함 확인
            sent_response = requests.get(
                f"{BASE_URL}/mail/sent",
                headers=headers
            )
            
            if sent_response.status_code == 200:
                sent_data = sent_response.json()
                sent_mails = sent_data.get("mails", [])
                if any(mail.get("mail_uuid") == mail_uuid for mail in sent_mails):
                    print("   ✅ 발신자 보낸편지함에 메일이 정상적으로 할당됨")
                else:
                    print("   ❌ 발신자 보낸편지함에 메일이 할당되지 않음")
            
            # 수신자의 받은편지함 확인
            recipient_token = get_auth_token("testuser1@example.com", "testpassword123")
            recipient_headers = {
                "Authorization": f"Bearer {recipient_token}",
                "Content-Type": "application/json"
            }
            
            inbox_response = requests.get(
                f"{BASE_URL}/mail/inbox",
                headers=recipient_headers
            )
            
            if inbox_response.status_code == 200:
                inbox_mails = inbox_response.json()
                if any(mail.get("mail_uuid") == mail_uuid for mail in inbox_mails):
                    print("   ✅ 수신자 받은편지함에 메일이 정상적으로 할당됨")
                else:
                    print("   ❌ 수신자 받은편지함에 메일이 할당되지 않음")
            
            return True
            
        else:
            print(f"   ❌ 메일 발송 실패: {send_response.status_code} - {send_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ 테스트 중 오류 발생: {str(e)}")
        return False

def test_draft_mail_folder_assignment():
    """임시저장 메일의 폴더 자동 할당 테스트"""
    
    print("\n📝 임시저장 메일 폴더 자동 할당 테스트 시작...")
    
    try:
        # 사용자 로그인
        token = get_auth_token("testuser2@example.com", "testpassword123")
        
        # 임시저장 메일 데이터 (Form 형식)
        draft_data = {
            "to_emails": "testuser1@example.com",
            "subject": f"임시저장 테스트 메일 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "content": "이 메일은 임시저장 폴더 자동 할당 로직을 테스트하기 위한 메일입니다.",
            "priority": "normal"
        }
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        # 임시저장 메일 생성 (Form 데이터로 전송)
        draft_response = requests.post(
            f"{BASE_URL}/mail/drafts",
            headers=headers,
            data=draft_data
        )
        
        if draft_response.status_code == 200:
            result = draft_response.json()
            mail_uuid = result.get("mail_uuid")
            print(f"   ✅ 임시저장 메일 생성 성공: mail_uuid={mail_uuid}")
            
            # 임시보관함 확인
            drafts_response = requests.get(
                f"{BASE_URL}/mail/drafts",
                headers=headers
            )
            
            if drafts_response.status_code == 200:
                draft_response_data = drafts_response.json()
                draft_mails = draft_response_data.get("mails", [])
                if any(mail.get("mail_uuid") == mail_uuid for mail in draft_mails):
                    print("   ✅ 임시보관함에 메일이 정상적으로 할당됨")
                    return True
                else:
                    print("   ❌ 임시보관함에 메일이 할당되지 않음")
                    return False
            else:
                print(f"   ❌ 임시보관함 조회 실패: {drafts_response.status_code}")
                return False
            
        else:
            print(f"   ❌ 임시저장 메일 생성 실패: {draft_response.status_code} - {draft_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ 테스트 중 오류 발생: {str(e)}")
        return False

def test_folder_statistics():
    """폴더별 메일 통계 확인"""
    
    print("\n📊 폴더별 메일 통계 확인...")
    
    try:
        # 사용자별 폴더 통계 확인
        users = [
            ("testuser1@example.com", "testpassword123"),
            ("testuser2@example.com", "testpassword123")
        ]
        
        for email, password in users:
            print(f"\n👤 사용자: {email}")
            
            token = get_auth_token(email, password)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # 받은편지함
            inbox_response = requests.get(f"{BASE_URL}/mail/inbox", headers=headers)
            if inbox_response.status_code == 200:
                inbox_data = inbox_response.json()
                inbox_count = len(inbox_data.get("mails", [])) if isinstance(inbox_data, dict) else len(inbox_data)
            else:
                inbox_count = 0
            print(f"   📥 받은편지함: {inbox_count}개")
            
            # 보낸편지함
            sent_response = requests.get(f"{BASE_URL}/mail/sent", headers=headers)
            if sent_response.status_code == 200:
                sent_data = sent_response.json()
                sent_count = len(sent_data.get("mails", [])) if isinstance(sent_data, dict) else len(sent_data)
            else:
                sent_count = 0
            print(f"   📤 보낸편지함: {sent_count}개")
            
            # 임시보관함
            drafts_response = requests.get(f"{BASE_URL}/mail/drafts", headers=headers)
            if drafts_response.status_code == 200:
                drafts_data = drafts_response.json()
                drafts_count = len(drafts_data.get("mails", [])) if isinstance(drafts_data, dict) else len(drafts_data)
            else:
                drafts_count = 0
            print(f"   📝 임시보관함: {drafts_count}개")
            
    except Exception as e:
        print(f"   ❌ 통계 확인 중 오류 발생: {str(e)}")

def main():
    """메인 테스트 함수"""
    
    print("🚀 메일 폴더 자동 할당 로직 테스트 시작")
    print("=" * 60)
    
    # 서버 상태 확인
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ 서버가 실행되지 않았습니다. 먼저 서버를 시작해주세요.")
            return
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. 먼저 서버를 시작해주세요.")
        return
    
    print("✅ 서버 연결 확인됨")
    
    # 테스트 실행
    test_results = []
    
    # 1. 메일 발송 테스트
    test_results.append(test_send_mail_folder_assignment())
    
    # 2. 임시저장 메일 테스트
    test_results.append(test_draft_mail_folder_assignment())
    
    # 3. 폴더 통계 확인
    test_folder_statistics()
    
    # 결과 요약
    print(f"\n📋 테스트 결과 요약:")
    print("=" * 60)
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print(f"✅ 통과한 테스트: {passed_tests}/{total_tests}")
    print(f"❌ 실패한 테스트: {total_tests - passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 모든 테스트가 성공적으로 통과했습니다!")
    else:
        print("⚠️ 일부 테스트가 실패했습니다. 로그를 확인해주세요.")

if __name__ == "__main__":
    main()