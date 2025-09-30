#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
경성 조직과 moonsoo 사용자 생성 스크립트
"""

import os
import sys
import requests
import json
from datetime import datetime
import uuid

# 환경 변수 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'

def create_organization_via_api():
    """API를 통해 경성 조직을 생성합니다."""
    try:
        url = "http://localhost:8000/api/v1/debug/create-organization"
        
        org_data = {
            "name": "경성대학교",
            "org_code": "KYUNGSUNG", 
            "domain": "kyungsung.ac.kr",
            "max_users": 1000,
            "is_active": True
        }
        
        print("🏢 경성대학교 조직 생성을 시도합니다...")
        print(f"조직명: {org_data['name']}")
        print(f"조직 코드: {org_data['org_code']}")
        print(f"도메인: {org_data['domain']}")
        
        response = requests.post(
            url,
            json=org_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 경성대학교 조직 생성 성공!")
            print(f"조직 ID: {result.get('id')}")
            print(f"조직 UUID: {result.get('org_uuid')}")
            return result
        else:
            print(f"❌ 조직 생성 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API 요청 실패: {e}")
        return None
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return None

def create_user_via_api(organization_id):
    """API를 통해 moonsoo 사용자를 생성합니다."""
    try:
        url = "http://localhost:8000/api/v1/debug/create-user"
        
        user_data = {
            "email": "moonsoo@kyungsung.ac.kr",
            "password": "test123",
            "full_name": "문수",
            "organization_id": organization_id,
            "role": "user",
            "is_active": True
        }
        
        print("\n👤 moonsoo 사용자 생성을 시도합니다...")
        print(f"이메일: {user_data['email']}")
        print(f"이름: {user_data['full_name']}")
        print(f"조직 ID: {user_data['organization_id']}")
        
        response = requests.post(
            url,
            json=user_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ moonsoo 사용자 생성 성공!")
            print(f"사용자 ID: {result.get('id')}")
            print(f"사용자 UUID: {result.get('user_uuid')}")
            return result
        else:
            print(f"❌ 사용자 생성 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API 요청 실패: {e}")
        return None
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return None

def login_and_get_token():
    """moonsoo 사용자로 로그인하여 토큰을 받습니다."""
    try:
        url = "http://localhost:8000/api/v1/auth/login"
        
        login_data = {
            "email": "moonsoo@kyungsung.ac.kr",
            "password": "test123"
        }
        
        print("\n🔐 moonsoo 사용자 로그인을 시도합니다...")
        
        response = requests.post(
            url,
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 로그인 성공!")
            print(f"액세스 토큰: {result.get('access_token')[:50]}...")
            return result.get('access_token')
        else:
            print(f"❌ 로그인 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API 요청 실패: {e}")
        return None
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return None

def send_test_email(access_token):
    """테스트 메일을 moon4656@gmail.com으로 발송합니다."""
    try:
        url = "http://localhost:8000/api/v1/mail/send"
        
        mail_data = {
            "to_email": "moon4656@gmail.com",
            "subject": "SkyBoot Mail 테스트 - 경성대학교에서 발송",
            "body": """안녕하세요!

이 메일은 SkyBoot Mail 시스템에서 발송된 테스트 메일입니다.

발송자: moonsoo@kyungsung.ac.kr (경성대학교)
발송 시간: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """

시스템이 정상적으로 작동하고 있습니다.

감사합니다.
SkyBoot Mail 시스템"""
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        print("\n📧 테스트 메일 발송을 시도합니다...")
        print(f"수신자: {mail_data['to_email']}")
        print(f"제목: {mail_data['subject']}")
        
        response = requests.post(
            url,
            json=mail_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 메일 발송 성공!")
            print(f"메일 ID: {result.get('mail_id')}")
            return result
        else:
            print(f"❌ 메일 발송 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API 요청 실패: {e}")
        return None
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return None

def main():
    """메인 실행 함수"""
    print("🚀 SkyBoot Mail 시스템 설정을 시작합니다...")
    print("=" * 60)
    
    # 1. 조직 생성
    org_result = create_organization_via_api()
    if not org_result:
        print("❌ 조직 생성에 실패했습니다. 프로그램을 종료합니다.")
        return False
    
    organization_id = org_result.get('org_id')
    
    # 2. 사용자 생성
    user_result = create_user_via_api(organization_id)
    if not user_result:
        print("❌ 사용자 생성에 실패했습니다. 프로그램을 종료합니다.")
        return False
    
    # 3. 로그인
    access_token = login_and_get_token()
    if not access_token:
        print("❌ 로그인에 실패했습니다. 프로그램을 종료합니다.")
        return False
    
    # 4. 테스트 메일 발송
    mail_result = send_test_email(access_token)
    if not mail_result:
        print("❌ 메일 발송에 실패했습니다.")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 모든 작업이 성공적으로 완료되었습니다!")
    print("✅ 경성대학교 조직 생성 완료")
    print("✅ moonsoo 사용자 생성 완료")
    print("✅ 로그인 성공")
    print("✅ 테스트 메일 발송 완료")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)