#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
수정된 메일 발송 테스트 스크립트
attachments 필드 오류 해결
"""

import requests
import json
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_mail_send_fixed():
    """
    수정된 메일 발송 테스트 - attachments 오류 해결
    """
    base_url = "http://localhost:8000"
    
    # 1. 로그인 (기존 사용자 사용)
    login_url = f"{base_url}/api/v1/auth/login"
    login_data = {
        "user_id": "user01",  # 또는 실제 존재하는 사용자 ID
        "password": "test"
    }
    
    logger.info("🔐 로그인 시도...")
    try:
        login_response = requests.post(login_url, json=login_data)
        logger.info(f"로그인 응답 상태: {login_response.status_code}")
        logger.info(f"로그인 응답 내용: {login_response.text}")
        
        if login_response.status_code != 200:
            logger.error("❌ 로그인 실패")
            return
            
        token = login_response.json().get("access_token")
        if not token:
            logger.error("❌ 토큰 획득 실패")
            return
            
        logger.info("✅ 로그인 성공")
        
    except Exception as e:
        logger.error(f"❌ 로그인 중 오류: {e}")
        return
    
    # 2. 메일 발송 (첨부파일 없이) - 수정된 방법
    mail_url = f"{base_url}/mail/send"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 첨부파일 필드를 아예 제외하고 전송
    mail_data = {
        'to_emails': 'moon4656@gmail.com',
        'subject': '🔧 수정된 테스트 메일',
        'content': '안녕하세요!\n\nattachments 오류를 수정한 테스트 메일입니다.\n\n감사합니다.'
    }
    
    logger.info("📤 메일 발송 시도...")
    logger.info(f"발송 데이터: {mail_data}")
    
    try:
        mail_response = requests.post(mail_url, data=mail_data, headers=headers)
        logger.info(f"메일 발송 응답 상태: {mail_response.status_code}")
        logger.info(f"메일 발송 응답 내용: {mail_response.text}")
        
        if mail_response.status_code == 200:
            logger.info("✅ 메일 발송 성공!")
            response_data = mail_response.json()
            logger.info(f"메일 ID: {response_data.get('mail_uuid', 'N/A')}")
        else:
            logger.error("❌ 메일 발송 실패")
            
    except Exception as e:
        logger.error(f"❌ 메일 발송 중 오류: {e}")

def test_mail_send_with_attachment():
    """
    첨부파일과 함께 메일 발송 테스트 (올바른 방법)
    """
    base_url = "http://localhost:8000/api/v1"
    
    # 임시 테스트 파일 생성
    test_file_content = "이것은 테스트 첨부파일입니다.\nattachments 필드 테스트용입니다."
    with open("test_attachment.txt", "w", encoding="utf-8") as f:
        f.write(test_file_content)
    
    # 로그인 (위와 동일)
    login_url = f"{base_url}/auth/login"
    login_data = {
        "user_id": "user01",
        "password": "test"
    }
    
    logger.info("🔐 첨부파일 테스트용 로그인...")
    try:
        login_response = requests.post(login_url, json=login_data)
        if login_response.status_code != 200:
            logger.error("❌ 로그인 실패")
            return
            
        token = login_response.json().get("access_token")
        if not token:
            logger.error("❌ 토큰 획득 실패")
            return
            
    except Exception as e:
        logger.error(f"❌ 로그인 중 오류: {e}")
        return
    
    # 첨부파일과 함께 메일 발송
    mail_url = f"{base_url}/mail/send"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 올바른 첨부파일 전송 방법
    with open("test_attachment.txt", "rb") as f:
        files = [('attachments', ('test_attachment.txt', f, 'text/plain'))]
        data = {
            'to_emails': 'moon4656@gmail.com',
            'subject': '📎 첨부파일 테스트 메일',
            'content': '첨부파일이 포함된 테스트 메일입니다.'
        }
        
        logger.info("📎 첨부파일과 함께 메일 발송...")
        try:
            mail_response = requests.post(mail_url, data=data, files=files, headers=headers)
            logger.info(f"첨부파일 메일 응답 상태: {mail_response.status_code}")
            logger.info(f"첨부파일 메일 응답 내용: {mail_response.text}")
            
            if mail_response.status_code == 200:
                logger.info("✅ 첨부파일 메일 발송 성공!")
            else:
                logger.error("❌ 첨부파일 메일 발송 실패")
                
        except Exception as e:
            logger.error(f"❌ 첨부파일 메일 발송 중 오류: {e}")

if __name__ == "__main__":
    logger.info("🔧 수정된 메일 발송 테스트 시작")
    logger.info("=" * 50)
    
    # 1. 첨부파일 없는 메일 테스트
    logger.info("1️⃣ 첨부파일 없는 메일 발송 테스트")
    test_mail_send_fixed()
    
    logger.info("\n" + "=" * 50)
    
    # 2. 첨부파일 있는 메일 테스트
    logger.info("2️⃣ 첨부파일 있는 메일 발송 테스트")
    test_mail_send_with_attachment()
    
    logger.info("\n🏁 테스트 완료")