#!/usr/bin/env python3
"""
완전한 메일 시스템 테스트 스크립트
사용자 등록, 로그인, 메일 발송을 순차적으로 테스트합니다.
"""

import requests
import uuid
import json

def test_mail_system():
    """메일 시스템 전체 기능을 테스트합니다."""
    
    # 고유한 사용자명과 이메일 생성
    unique_id = str(uuid.uuid4())[:8]
    username = f'mailtest_{unique_id}'
    email = f'{username}@example.com'

    print(f'새 사용자 생성: {username}, {email}')

    # 1. 사용자 등록 (메일 사용자도 함께 생성됨)
    register_data = {
        'username': username,
        'email': email,
        'password': 'test123',
        'full_name': f'Mail Test User {unique_id}',
        'org_name': 'SkyBoot'
    }

    register_response = requests.post('http://localhost:8000/api/v1/auth/register', json=register_data)
    print(f'사용자 등록 상태: {register_response.status_code}')

    if register_response.status_code == 201:
        print('✅ 사용자 등록 성공!')
        user_data = register_response.json()
        print(f'등록된 사용자: {user_data["username"]} ({user_data["email"]})')
        
        # 2. 로그인
        login_data = {
            'email': email,
            'password': 'test123'
        }
        
        login_response = requests.post('http://localhost:8000/api/v1/auth/login', json=login_data)
        print(f'\n로그인 상태: {login_response.status_code}')
        
        if login_response.status_code == 200:
            print('✅ 로그인 성공!')
            token = login_response.json()['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # 3. 메일 발송 테스트
            recipient_email = f'recipient_{str(uuid.uuid4())[:8]}@example.com'
            mail_data = {
                'to_emails': recipient_email,
                'subject': 'WSL Postfix 테스트 메일',
                'content': '안녕하세요! WSL Postfix 연동 테스트 메일입니다.',
                'priority': 'normal'
            }
            
            mail_response = requests.post('http://localhost:8000/api/v1/mail/send', data=mail_data, headers=headers)
            print(f'\n메일 발송 상태: {mail_response.status_code}')
            if mail_response.status_code == 200:
                print('✅ 메일 발송 성공!')
                response_data = mail_response.json()
                print(f'메일 ID: {response_data.get("mail_id", "N/A")}')
                print(f'메시지: {response_data.get("message", "N/A")}')
                return True
            else:
                print(f'❌ 메일 발송 실패: {mail_response.text}')
                return False
        else:
            print(f'❌ 로그인 실패: {login_response.text}')
            return False
    else:
        print(f'❌ 사용자 등록 실패: {register_response.text}')
        return False

if __name__ == "__main__":
    success = test_mail_system()
    if success:
        print('\n🎉 모든 테스트가 성공적으로 완료되었습니다!')
    else:
        print('\n❌ 테스트 중 오류가 발생했습니다.')