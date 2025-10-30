#!/usr/bin/env python3
"""
환경 변수 로딩 디버그 스크립트
"""

import os
from dotenv import load_dotenv

print("🔍 환경 변수 디버그 시작")

# .env 파일 로드
print("\n📁 .env 파일 로드 시도...")
load_dotenv()
print("✅ .env 파일 로드 완료")

# SMTP 관련 환경 변수 확인
smtp_vars = [
    "ENVIRONMENT",
    "SMTP_HOST", 
    "SMTP_PORT", 
    "SMTP_USER", 
    "SMTP_PASSWORD", 
    "SMTP_FROM_EMAIL",
    "SMTP_USE_TLS"
]

print("\n📧 SMTP 환경 변수 확인:")
for var in smtp_vars:
    value = os.getenv(var)
    if var == "SMTP_PASSWORD" and value:
        value = "*" * len(value)  # 비밀번호 마스킹
    print(f"   {var}: {value}")

# config.py 설정 확인
print("\n⚙️ Config 설정 확인:")
try:
    from app.config import settings
    print(f"   ENVIRONMENT: {settings.ENVIRONMENT}")
    print(f"   DEFAULT_SMTP_HOST: {settings.DEFAULT_SMTP_HOST}")
    print(f"   DEFAULT_SMTP_PORT: {settings.DEFAULT_SMTP_PORT}")
    print(f"   DEFAULT_SMTP_USER: {settings.DEFAULT_SMTP_USER}")
    print(f"   DEFAULT_SMTP_FROM_EMAIL: {settings.DEFAULT_SMTP_FROM_EMAIL}")
    
    # SMTP 설정 가져오기
    smtp_config = settings.get_smtp_config()
    print(f"\n📤 get_smtp_config() 결과:")
    for key, value in smtp_config.items():
        if key == "password" and value:
            value = "*" * len(value)
        print(f"   {key}: {value}")
        
except Exception as e:
    print(f"❌ Config 로드 오류: {e}")

print("\n🔍 환경 변수 디버그 완료")