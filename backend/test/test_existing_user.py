#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기존 사용자로 로그인 테스트 스크립트
"""

import requests
import json

def test_login_existing_user():
    """기존 사용자로 로그인을 테스트합니다"""
    
    # 기존 사용자 정보 (데이터베이스에서 확인된 사용자)
    login_data = {
        "email": "test@example.com",
        "password": "test123456"  # 일반적인 테스트 비밀번호
    }
    
    try:
        print("🔐 기존 사용자 로그인 테스트 시작...")
        print(f"📧 이메일: {login_data['email']}")
        
        response = requests.post(
            "http://localhost:8000/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📊 응답 상태 코드: {response.status_code}")
        
        try:
            response_json = response.json()
            print(f"📝 응답 내용: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
        except:
            print(f"📝 응답 내용 (텍스트): {response.text}")
        
        if response.status_code == 200:
            print("✅ 로그인 성공!")
            return response_json.get('access_token')
        else:
            print(f"❌ 로그인 실패: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return None

def test_register_new_user():
    """새로운 사용자로 회원가입을 테스트합니다"""
    
    # 새로운 사용자 정보
    register_data = {
        "email": "test@skyboot.com",
        "username": "skybootuser",  # 다른 사용자명 사용
        "password": "test123456"
    }
    
    try:
        print("\n🚀 새 사용자 회원가입 테스트 시작...")
        print(f"📧 이메일: {register_data['email']}")
        print(f"👤 사용자명: {register_data['username']}")
        
        response = requests.post(
            "http://localhost:8000/auth/register",
            json=register_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📊 응답 상태 코드: {response.status_code}")
        
        try:
            response_json = response.json()
            print(f"📝 응답 내용: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
        except:
            print(f"📝 응답 내용 (텍스트): {response.text}")
        
        if response.status_code == 201:
            print("✅ 회원가입 성공!")
            return True
        else:
            print(f"❌ 회원가입 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return False

def test_login_new_user():
    """새로 가입한 사용자로 로그인을 테스트합니다"""
    
    login_data = {
        "email": "test@skyboot.com",
        "password": "test123456"
    }
    
    try:
        print("\n🔐 새 사용자 로그인 테스트 시작...")
        print(f"📧 이메일: {login_data['email']}")
        
        response = requests.post(
            "http://localhost:8000/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📊 응답 상태 코드: {response.status_code}")
        
        try:
            response_json = response.json()
            print(f"📝 응답 내용: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
        except:
            print(f"📝 응답 내용 (텍스트): {response.text}")
        
        if response.status_code == 200:
            print("✅ 로그인 성공!")
            return response_json.get('access_token')
        else:
            print(f"❌ 로그인 실패: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 사용자 인증 종합 테스트")
    print("=" * 60)
    
    # 1. 기존 사용자 로그인 테스트
    existing_token = test_login_existing_user()
    
    # 2. 새 사용자 회원가입 테스트
    register_success = test_register_new_user()
    
    # 3. 새 사용자 로그인 테스트
    new_token = None
    if register_success:
        new_token = test_login_new_user()
    
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    print(f"기존 사용자 로그인: {'✅ 성공' if existing_token else '❌ 실패'}")
    print(f"새 사용자 회원가입: {'✅ 성공' if register_success else '❌ 실패'}")
    print(f"새 사용자 로그인: {'✅ 성공' if new_token else '❌ 실패'}")
    
    if new_token:
        print(f"\n🔑 새 사용자 액세스 토큰: {new_token[:50]}...")