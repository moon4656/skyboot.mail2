#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
회원가입 테스트 스크립트
"""

import requests
import json

def test_register():
    """회원가입을 테스트합니다"""
    
    # 회원가입 데이터
    register_data = {
        "email": "test@skyboot.com",
        "username": "testuser",
        "password": "test123456"
    }
    
    try:
        print("🚀 회원가입 테스트 시작...")
        print(f"📧 이메일: {register_data['email']}")
        print(f"👤 사용자명: {register_data['username']}")
        
        response = requests.post(
            "http://localhost:8000/auth/register",
            json=register_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📊 응답 상태 코드: {response.status_code}")
        print(f"📄 응답 헤더: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            print(f"📝 응답 내용: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
        except:
            print(f"📝 응답 내용 (텍스트): {response.text}")
        
        if response.status_code == 201:
            print("✅ 회원가입 성공!")
            return True
        elif response.status_code == 400:
            print("⚠️ 이미 등록된 사용자이거나 잘못된 요청")
            return False
        else:
            print(f"❌ 회원가입 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return False

def test_login():
    """로그인을 테스트합니다"""
    
    login_data = {
        "email": "test@skyboot.com",
        "password": "test123456"
    }
    
    try:
        print("\n🔐 로그인 테스트 시작...")
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
            return True
        else:
            print(f"❌ 로그인 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 인증 API 테스트")
    print("=" * 50)
    
    # 회원가입 테스트
    register_success = test_register()
    
    # 로그인 테스트
    login_success = test_login()
    
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약")
    print("=" * 50)
    print(f"회원가입: {'✅ 성공' if register_success else '❌ 실패'}")
    print(f"로그인: {'✅ 성공' if login_success else '❌ 실패'}")