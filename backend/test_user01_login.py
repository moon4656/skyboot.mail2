import requests
import json

# API 서버 URL
BASE_URL = 'http://localhost:8000/api/v1'

try:
    print('=== user01 로그인 테스트 ===')
    
    # 1. user01로 로그인 시도 (일반적인 비밀번호들로 시도)
    passwords_to_try = ['test']
    
    for password in passwords_to_try:
        print(f'비밀번호 "{password}"로 시도 중...')
        
        login_data = {
            'user_id': 'user01',
            'password': password
        }
        
        login_response = requests.post(f'{BASE_URL}/auth/login', json=login_data)
        print(f'응답 코드: {login_response.status_code}')
        
        if login_response.status_code == 200:
            print(f'✅ 로그인 성공! 비밀번호: {password}')
            
            # 토큰 추출
            token_data = login_response.json()
            token = token_data['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            print(f'액세스 토큰: {token[:50]}...')
            
            # 사용자 정보 확인
            profile_response = requests.get(f'{BASE_URL}/users/profile', headers=headers)
            if profile_response.status_code == 200:
                profile = profile_response.json()
                print(f'사용자 정보: {profile.get("email", "N/A")} - {profile.get("role", "N/A")}')
            
            break
        else:
            print(f'❌ 로그인 실패: {login_response.text}')
    else:
        print('❌ 모든 비밀번호 시도 실패')

except Exception as e:
    print(f'❌ 오류 발생: {e}')
    import traceback
    traceback.print_exc()