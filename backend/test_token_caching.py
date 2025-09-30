#!/usr/bin/env python3
"""
토큰 캐싱 기능 테스트 스크립트
"""
import sys
import os
sys.path.insert(0, '.')
from fastapi.testclient import TestClient
from main import app
from test.auth_utils import TestAuthUtils
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_token_caching():
    """토큰 캐싱 기능을 테스트합니다."""
    client = TestClient(app)
    
    print('🔍 개선된 토큰 캐싱 기능 테스트...')
    
    # 캐시 초기화
    TestAuthUtils.clear_token_cache()
    
    # 첫 번째 토큰 생성 (새로 생성됨)
    print('\n1️⃣ 첫 번째 관리자 토큰 생성:')
    token1 = TestAuthUtils.get_admin_token(client)
    print(f'토큰 생성: {"✅" if token1 else "❌"}')
    
    # 두 번째 토큰 생성 (캐시에서 가져옴)
    print('\n2️⃣ 두 번째 관리자 토큰 생성 (캐시 사용):')
    token2 = TestAuthUtils.get_admin_token(client)
    print(f'토큰 생성: {"✅" if token2 else "❌"}')
    print(f'토큰 동일성: {"✅" if token1 == token2 else "❌"}')
    
    # 헤더 생성 테스트
    print('\n3️⃣ 인증 헤더 생성 테스트:')
    headers = TestAuthUtils.get_auth_headers(client, is_admin=True)
    print(f'헤더 생성: {"✅" if "Authorization" in headers else "❌"}')
    
    # API 호출 테스트
    print('\n4️⃣ API 호출 테스트:')
    response = client.get('/api/v1/organizations/current', headers=headers)
    print(f'API 응답: {response.status_code}')
    print(f'API 성공: {"✅" if response.status_code == 200 else "❌"}')
    
    print('\n🎯 토큰 캐싱 테스트 완료!')

if __name__ == "__main__":
    test_token_caching()