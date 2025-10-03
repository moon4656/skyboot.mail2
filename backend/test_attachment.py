#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
첨부파일 기능 테스트 스크립트
SkyBoot Mail SaaS 프로젝트의 첨부파일 발송 및 다운로드 기능을 테스트합니다.
"""

import requests
import json
import os
import tempfile
from typing import Dict, Any

# API 기본 설정
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def create_test_file(filename: str, content: str) -> str:
    """
    테스트용 파일을 생성합니다.
    
    Args:
        filename: 생성할 파일명
        content: 파일 내용
    
    Returns:
        생성된 파일의 경로
    """
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"📄 테스트 파일 생성: {file_path}")
    return file_path

def login_and_get_token() -> str:
    """
    로그인하여 JWT 토큰을 획득합니다.
    
    Returns:
        JWT 액세스 토큰
    """
    login_url = f"{API_BASE}/auth/login"
    
    # 테스트용 로그인 정보 (실제 환경에 맞게 수정 필요)
    login_data = {
        "user_id": "user01",
        "password": "test"
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print(f"✅ 로그인 성공: {access_token[:20]}...")
            return access_token
        else:
            print(f"❌ 로그인 실패: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 로그인 요청 오류: {str(e)}")
        return None

def test_send_mail_with_attachment(token: str, attachment_path: str) -> Dict[str, Any]:
    """
    첨부파일이 포함된 메일 발송을 테스트합니다.
    
    Args:
        token: JWT 액세스 토큰
        attachment_path: 첨부파일 경로
    
    Returns:
        API 응답 결과
    """
    send_url = f"{API_BASE}/mail/send"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Form 데이터 준비
    form_data = {
        "to_emails": "test@example.com",
        "subject": "첨부파일 테스트 메일",
        "content": "이 메일은 첨부파일 기능을 테스트하기 위한 메일입니다.\n\n첨부파일이 정상적으로 업로드되고 저장되는지 확인해주세요.",
        "priority": "normal"
    }
    
    # 첨부파일 준비
    files = []
    if os.path.exists(attachment_path):
        files.append(('attachments', (os.path.basename(attachment_path), open(attachment_path, 'rb'), 'text/plain')))
    
    try:
        print(f"📤 첨부파일 포함 메일 발송 시작...")
        print(f"   - 수신자: {form_data['to_emails']}")
        print(f"   - 제목: {form_data['subject']}")
        print(f"   - 첨부파일: {os.path.basename(attachment_path)}")
        
        response = requests.post(send_url, headers=headers, data=form_data, files=files)
        
        # 파일 핸들 닫기
        for _, file_tuple in files:
            if len(file_tuple) > 1 and hasattr(file_tuple[1], 'close'):
                file_tuple[1].close()
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 메일 발송 성공!")
            print(f"   - 메일 UUID: {result.get('mail_uuid')}")
            print(f"   - 발송 시간: {result.get('sent_at')}")
            return result
        else:
            print(f"❌ 메일 발송 실패: {response.status_code}")
            print(f"   - 응답: {response.text}")
            return {"success": False, "error": response.text}
            
    except Exception as e:
        print(f"❌ 메일 발송 요청 오류: {str(e)}")
        return {"success": False, "error": str(e)}

def test_get_sent_mails(token: str) -> Dict[str, Any]:
    """
    보낸 메일함을 조회하여 첨부파일 정보를 확인합니다.
    
    Args:
        token: JWT 액세스 토큰
    
    Returns:
        API 응답 결과
    """
    sent_url = f"{API_BASE}/mail/sent"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        print(f"📋 보낸 메일함 조회...")
        response = requests.get(sent_url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            mails = result.get('mails', [])
            print(f"✅ 보낸 메일함 조회 성공! (총 {len(mails)}개)")
            
            # 최근 메일 정보 출력
            if mails:
                latest_mail = mails[0]
                print(f"   - 최근 메일 UUID: {latest_mail.get('mail_uuid')}")
                print(f"   - 제목: {latest_mail.get('subject')}")
                print(f"   - 첨부파일 수: {len(latest_mail.get('attachments', []))}")
                
                # 첨부파일 정보 출력
                for attachment in latest_mail.get('attachments', []):
                    print(f"     📎 {attachment.get('filename')} ({attachment.get('file_size')} bytes)")
            
            return result
        else:
            print(f"❌ 보낸 메일함 조회 실패: {response.status_code}")
            print(f"   - 응답: {response.text}")
            return {"success": False, "error": response.text}
            
    except Exception as e:
        print(f"❌ 보낸 메일함 조회 오류: {str(e)}")
        return {"success": False, "error": str(e)}

def test_download_attachment(token: str, attachment_id: str) -> bool:
    """
    첨부파일 다운로드를 테스트합니다.
    
    Args:
        token: JWT 액세스 토큰
        attachment_id: 첨부파일 ID
    
    Returns:
        다운로드 성공 여부
    """
    download_url = f"{API_BASE}/mail/attachments/{attachment_id}"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        print(f"📥 첨부파일 다운로드 테스트...")
        print(f"   - 첨부파일 ID: {attachment_id}")
        
        response = requests.get(download_url, headers=headers)
        
        if response.status_code == 200:
            # 다운로드된 파일 크기 확인
            content_length = len(response.content)
            print(f"✅ 첨부파일 다운로드 성공!")
            print(f"   - 파일 크기: {content_length} bytes")
            print(f"   - Content-Type: {response.headers.get('content-type', 'unknown')}")
            return True
        else:
            print(f"❌ 첨부파일 다운로드 실패: {response.status_code}")
            print(f"   - 응답: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 첨부파일 다운로드 오류: {str(e)}")
        return False

def main():
    """
    메인 테스트 함수
    첨부파일 기능의 전체 플로우를 테스트합니다.
    """
    print("🧪 SkyBoot Mail 첨부파일 기능 테스트 시작")
    print("=" * 50)
    
    # 1. 테스트 파일 생성
    test_content = """이것은 첨부파일 테스트를 위한 샘플 텍스트 파일입니다.

SkyBoot Mail SaaS 프로젝트의 첨부파일 기능을 테스트하고 있습니다.

테스트 내용:
- 파일 업로드
- 파일 저장
- 파일 다운로드
- 메일 발송

작성일: 2024년
프로젝트: SkyBoot Mail SaaS
"""
    
    test_file_path = create_test_file("skyboot_test_attachment.txt", test_content)
    
    try:
        # 2. 로그인 및 토큰 획득
        print("\n🔐 로그인 테스트")
        print("-" * 30)
        token = login_and_get_token()
        
        if not token:
            print("❌ 로그인에 실패하여 테스트를 중단합니다.")
            return
        
        # 3. 첨부파일 포함 메일 발송 테스트
        print("\n📤 첨부파일 포함 메일 발송 테스트")
        print("-" * 30)
        send_result = test_send_mail_with_attachment(token, test_file_path)
        
        if not send_result.get("success", False):
            print("❌ 메일 발송에 실패하여 테스트를 중단합니다.")
            return
        
        # 4. 보낸 메일함 조회 테스트
        print("\n📋 보낸 메일함 조회 테스트")
        print("-" * 30)
        sent_result = test_get_sent_mails(token)
        
        # 5. 첨부파일 다운로드 테스트 (첨부파일 ID가 있는 경우)
        if sent_result.get("mails") and len(sent_result["mails"]) > 0:
            latest_mail = sent_result["mails"][0]
            attachments = latest_mail.get("attachments", [])
            
            if attachments:
                print("\n📥 첨부파일 다운로드 테스트")
                print("-" * 30)
                attachment_id = attachments[0].get("attachment_uuid")
                if attachment_id:
                    test_download_attachment(token, attachment_id)
                else:
                    print("⚠️ 첨부파일 ID를 찾을 수 없습니다.")
            else:
                print("⚠️ 첨부파일이 없습니다.")
        
        print("\n🎉 첨부파일 기능 테스트 완료!")
        print("=" * 50)
        
    finally:
        # 테스트 파일 정리
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
            print(f"🗑️ 테스트 파일 삭제: {test_file_path}")

if __name__ == "__main__":
    main()