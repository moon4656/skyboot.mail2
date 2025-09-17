#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
사용자 비밀번호 확인 스크립트
"""

from app.database import SessionLocal
from app.models import User
from passlib.context import CryptContext

def check_user_password():
    """사용자 비밀번호를 확인합니다."""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.email == 'test@example.com').first()
        if user:
            print(f"사용자 정보: {user.email}")
            print(f"비밀번호 해시: {user.hashed_password}")
            
            pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
            
            # 여러 비밀번호 후보 테스트
            passwords = ['testpassword123', 'password123', 'test123', 'admin123']
            
            for pwd in passwords:
                is_valid = pwd_context.verify(pwd, user.hashed_password)
                print(f"비밀번호 '{pwd}' 검증: {is_valid}")
                if is_valid:
                    print(f"✅ 올바른 비밀번호: {pwd}")
                    return pwd
            
            print("❌ 올바른 비밀번호를 찾을 수 없습니다.")
        else:
            print("❌ 사용자를 찾을 수 없습니다.")
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    
    finally:
        session.close()

if __name__ == "__main__":
    check_user_password()