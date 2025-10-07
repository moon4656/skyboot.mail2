#!/usr/bin/env python3
"""
사용자 비밀번호 확인 및 테스트 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.model.user_model import User
from app.service.auth_service import AuthService
import bcrypt

def check_user_password():
    """사용자 비밀번호 확인"""
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # testuser_folder 사용자 찾기
        user = db.query(User).filter(User.email == "testuser_folder@example.com").first()
        
        if not user:
            print("❌ testuser_folder@example.com 사용자를 찾을 수 없습니다.")
            return
        
        print(f"✅ 사용자 정보:")
        print(f"   - user_id: {user.user_id}")
        print(f"   - email: {user.email}")
        print(f"   - username: {user.username}")
        print(f"   - org_id: {user.org_id}")
        print(f"   - is_active: {user.is_active}")
        print(f"   - hashed_password: {user.hashed_password[:50]}...")
        
        # 일반적인 비밀번호들 테스트
        common_passwords = [
            "password",
            "test",
            "123456",
            "testuser_folder",
            "testuser",
            "folder",
            "admin",
            "user",
            "1234",
            "qwerty",
            "abc123",
            "password123",
            "test123"
        ]
        
        print(f"\n🔍 일반적인 비밀번호 테스트:")
        for pwd in common_passwords:
            if AuthService.verify_password(pwd, user.hashed_password):
                print(f"✅ 비밀번호 발견: '{pwd}'")
                return pwd
            else:
                print(f"❌ '{pwd}' - 일치하지 않음")
        
        print(f"\n⚠️ 일반적인 비밀번호로는 찾을 수 없습니다.")
        
        # 비밀번호 재설정
        print(f"\n🔧 비밀번호를 'newpassword'로 재설정합니다...")
        new_password = "newpassword"
        user.hashed_password = AuthService.get_password_hash(new_password)
        db.commit()
        
        print(f"✅ 비밀번호가 '{new_password}'로 재설정되었습니다.")
        return new_password
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    password = check_user_password()
    if password:
        print(f"\n🎯 사용 가능한 비밀번호: {password}")