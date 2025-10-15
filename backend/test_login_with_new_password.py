#!/usr/bin/env python3
"""
변경된 패스워드 'test'로 로그인 테스트를 수행하는 스크립트
"""

import requests
import json

def test_login_with_new_password():
    """
    모든 사용자가 새 패스워드 'test'로 로그인할 수 있는지 테스트합니다.
    """
    print("=" * 80)
    print("🔐 새 패스워드 'test'로 로그인 테스트")
    print("=" * 80)
    
    # 테스트할 사용자 목록 (user01만 테스트)
    test_users = [
        {"user_id": "user01", "email": "user01@skyboot.mail", "password": "test", "role": "일반 사용자"}
    ]
    
    # API 엔드포인트
    login_url = "http://localhost:8000/api/v1/auth/login"
    
    success_count = 0
    total_count = len(test_users)
    
    for i, user in enumerate(test_users, 1):
        print(f"\n{i}. {user['role']} 로그인 테스트")
        print(f"   사용자 ID: {user['user_id']}")
        print(f"   이메일: {user['email']}")
        print(f"   패스워드: {user['password']}")
        
        try:
            # 로그인 요청 데이터 (UserLogin 스키마에 맞게)
            login_data = {
                "user_id": user["user_id"],  # user_id 필드 사용
                "password": user["password"]
            }
            
            # 로그인 API 호출
            response = requests.post(
                login_url,
                json=login_data,  # JSON으로 전송
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 로그인 성공!")
                print(f"   - 액세스 토큰: {result.get('access_token', 'N/A')[:50]}...")
                print(f"   - 토큰 타입: {result.get('token_type', 'N/A')}")
                success_count += 1
            else:
                print(f"   ❌ 로그인 실패!")
                print(f"   - 상태 코드: {response.status_code}")
                print(f"   - 응답: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ 연결 오류: FastAPI 서버가 실행 중인지 확인하세요.")
            print(f"   - 서버 주소: {login_url}")
        except Exception as e:
            print(f"   ❌ 오류 발생: {str(e)}")
    
    print("\n" + "=" * 80)
    print(f"📊 로그인 테스트 결과")
    print(f"   성공: {success_count}명 / 전체: {total_count}명")
    
    if success_count == total_count:
        print("✅ 모든 사용자의 패스워드가 성공적으로 'test'로 변경되었습니다!")
    else:
        print("⚠️  일부 사용자의 로그인에 문제가 있습니다.")
    
    print("=" * 80)

if __name__ == "__main__":
    test_login_with_new_password()