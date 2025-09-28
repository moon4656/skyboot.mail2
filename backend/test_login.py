#!/usr/bin/env python3
"""
로그인 테스트 스크립트
"""

import requests
import json

def test_login(email, password):
    """로그인 테스트 함수"""
    login_data = {
        'email': email,
        'password': password
    }
    
    try:
        response = requests.post(
            'http://localhost:8000/api/v1/auth/login',
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f'📧 이메일: {email}')
        print(f'📊 응답 코드: {response.status_code}')
        print(f'📄 응답 내용: {response.text}')
        
        if response.status_code == 200:
            token_data = response.json()
            print(f'✅ 로그인 성공!')
            print(f'🔑 토큰 타입: {token_data.get("token_type")}')
            print(f'⏰ 만료 시간: {token_data.get("expires_in")}')
            return True
        else:
            print(f'❌ 로그인 실패')
            return False
            
    except Exception as e:
        print(f'🚨 오류 발생: {e}')
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 로그인 테스트 시작")
    print("=" * 60)
    
    # 여러 계정으로 테스트
    test_accounts = [
        ("admin@test.com", "admin123"),
        ("admin@skyboot.com", "admin123"),
        ("testuser@example.com", "testpass123"),
        ("mailtest@example.com", "testpass123")
    ]
    
    for email, password in test_accounts:
        print(f"\n🔍 {email} 계정 테스트:")
        success = test_login(email, password)
        if success:
            print(f"✅ {email} 로그인 성공!")
            break
        print("-" * 40)
    
    print("\n" + "=" * 60)
    print("🏁 테스트 완료")
    print("=" * 60)