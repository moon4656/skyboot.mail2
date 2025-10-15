#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로그인 API 테스트 스크립트
"""

import requests
import json

def test_login_api():
    """로그인 API를 테스트합니다."""
    
    # 로그인 API 테스트
    login_url = 'http://localhost:8000/api/v1/auth/login'
    login_data = {
        'user_id': 'user01',
        'password': 'test'
    }

    try:
        print('로그인 API 테스트 시작...')
        print(f'URL: {login_url}')
        print(f'데이터: {login_data}')
        
        response = requests.post(login_url, json=login_data)
        
        print(f'\n응답 결과:')
        print(f'상태 코드: {response.status_code}')
        print(f'응답 헤더: {dict(response.headers)}')
        
        if response.status_code == 200:
            result = response.json()
            print(f'로그인 성공!')
            access_token = result.get('access_token', '없음')
            if len(access_token) > 50:
                print(f'토큰: {access_token[:50]}...')
            else:
                print(f'토큰: {access_token}')
        else:
            print(f'로그인 실패!')
            try:
                error_detail = response.json()
                print(f'오류 상세: {error_detail}')
            except:
                print(f'응답 텍스트: {response.text}')
                
    except Exception as e:
        print(f'요청 오류: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_login_api()