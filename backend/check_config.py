#!/usr/bin/env python3
"""
설정 확인 스크립트
"""

from app.config import settings

print("📋 현재 데이터베이스 설정:")
print(f"DATABASE_URL: {settings.DATABASE_URL}")
print(f"DB_HOST: {settings.DB_HOST}")
print(f"DB_PORT: {settings.DB_PORT}")
print(f"DB_USER: {settings.DB_USER}")
print(f"DB_PASSWORD: {settings.DB_PASSWORD}")
print(f"DB_NAME: {settings.DB_NAME}")