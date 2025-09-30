#!/usr/bin/env python3
"""
토큰 생성 상태 디버깅 스크립트
"""
import sys
import os
sys.path.insert(0, '.')
from fastapi.testclient import TestClient
from main import app
from test.auth_utils import TestAuthUtils

def debug_token_generation():
    """토큰 생성 상태를 디버깅합니다."""
    client = TestClient(app)
    
    print('🔍 토큰 생성 상태 디버깅...')
    
    # 캐시 초기화
    TestAuthUtils.clear_token_cache()
    
    # 관리자 토큰 생성
    print('\n1️⃣ 관리자 토큰 생성:')
    admin_token = TestAuthUtils.get_admin_token(client)
    print(f'관리자 토큰 생성: {"✅" if admin_token else "❌"}')
    print(f'토큰 길이: {len(admin_token) if admin_token else 0}')
    print(f'토큰 앞부분: {admin_token[:50] if admin_token else "None"}...')
    
    # 사용자 토큰 생성
    print('\n2️⃣ 사용자 토큰 생성:')
    user_token = TestAuthUtils.get_user_token(client)
    print(f'사용자 토큰 생성: {"✅" if user_token else "❌"}')
    print(f'토큰 길이: {len(user_token) if user_token else 0}')
    print(f'토큰 앞부분: {user_token[:50] if user_token else "None"}...')
    
    # 캐시 상태 확인
    print('\n3️⃣ 캐시 상태 확인:')
    print(f'캐시된 관리자 토큰: {"✅" if TestAuthUtils._cached_admin_token else "❌"}')
    print(f'캐시된 사용자 토큰: {"✅" if TestAuthUtils._cached_user_token else "❌"}')
    
    print('\n🎯 토큰 생성 디버깅 완료!')

if __name__ == "__main__":
    debug_token_generation()