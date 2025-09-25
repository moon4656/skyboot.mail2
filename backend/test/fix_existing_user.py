import requests
import json

# 기존 사용자로 로그인하여 메일 사용자 생성 확인
login_data = {
    "email": "test@example.com",
    "password": "testpassword123"
}

try:
    # 로그인 시도
    response = requests.post("http://localhost:8000/auth/login", json=login_data)
    print(f"Login response status: {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        print(f"Access token obtained: {access_token[:20]}...")
        
        # 인증 헤더 설정
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # inbox 테스트
        inbox_response = requests.get("http://localhost:8000/mail/inbox", headers=headers)
        print(f"Inbox response status: {inbox_response.status_code}")
        print(f"Inbox response: {inbox_response.text}")
        
    else:
        print(f"Login failed: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")