#!/usr/bin/env python3
"""
새로운 인증 유틸리티 테스트 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app
from auth_utils import TestAuthUtils, get_test_admin_token, get_test_user_token, get_test_auth_headers

def test_auth_utils():
    """새로운 인증 유틸리티 테스트"""
    print('🧪 새로운 인증 유틸리티 테스트 시작')
    print('=' * 50)

    # TestClient 생성
    client = TestClient(app)

    # 관리자 계정 검증
    print('1. 관리자 계정 검증 중...')
    if TestAuthUtils.verify_admin_account():
        print('✅ 관리자 계정 검증 성공')
    else:
        print('❌ 관리자 계정 검증 실패')

    # 관리자 토큰 생성 테스트
    print('\n2. 관리자 토큰 생성 테스트...')
    admin_token = get_test_admin_token(client)
    if admin_token:
        print('✅ 관리자 토큰 생성 성공')
        print(f'토큰 길이: {len(admin_token)} 문자')
        print(f'토큰 시작: {admin_token[:20]}...')
    else:
        print('❌ 관리자 토큰 생성 실패')

    # 사용자 토큰 생성 테스트
    print('\n3. 사용자 토큰 생성 테스트...')
    user_token = get_test_user_token(client)
    if user_token:
        print('✅ 사용자 토큰 생성 성공')
        print(f'토큰 길이: {len(user_token)} 문자')
    else:
        print('⚠️ 사용자 토큰 생성 실패 (사용자 계정이 없을 수 있음)')

    # 인증 헤더 생성 테스트
    print('\n4. 인증 헤더 생성 테스트...')
    admin_headers = get_test_auth_headers(client, is_admin=True)
    if 'Authorization' in admin_headers:
        print('✅ 관리자 인증 헤더 생성 성공')
    else:
        print('❌ 관리자 인증 헤더 생성 실패')

    user_headers = get_test_auth_headers(client, is_admin=False)
    if 'Authorization' in user_headers:
        print('✅ 사용자 인증 헤더 생성 성공')
    else:
        print('⚠️ 사용자 인증 헤더 생성 실패')

    # 토큰으로 API 호출 테스트
    print('\n5. 토큰으로 API 호출 테스트...')
    if admin_token:
        headers = {'Authorization': f'Bearer {admin_token}'}
        response = client.get('/api/v1/organizations/current', headers=headers)
        print(f'API 응답 상태: {response.status_code}')
        if response.status_code == 200:
            print('✅ 토큰을 사용한 API 호출 성공')
            data = response.json()
            print(f'조직 정보: {data.get("name", "N/A")}')
        else:
            print(f'❌ API 호출 실패: {response.text}')
    else:
        print('⏭️ 토큰이 없어 API 호출 테스트를 건너뜁니다.')

    print('\n🏁 테스트 완료')
    return admin_token is not None

if __name__ == "__main__":
    success = test_auth_utils()
    sys.exit(0 if success else 1)