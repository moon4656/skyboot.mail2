#!/usr/bin/env python3
"""
Admin 계정 정보 확인 스크립트
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.model.user_model import User
from app.service.auth_service import AuthService

def check_admin_account():
    """Admin 계정 정보 확인"""
    print("🔍 Admin 계정 정보 확인 중...")
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # admin@skyboot.com 계정 조회
        admin_user = db.query(User).filter(User.email == "admin@skyboot.com").first()
        
        if admin_user:
            print(f"✅ Admin 계정 발견:")
            print(f"   - 사용자 ID: {admin_user.user_id}")
            print(f"   - 이메일: {admin_user.email}")
            print(f"   - 사용자명: {admin_user.username}")
            print(f"   - 조직 ID: {admin_user.org_id}")
            print(f"   - 역할: {admin_user.role}")
            print(f"   - 활성 상태: {admin_user.is_active}")
            print(f"   - 생성일: {admin_user.created_at}")
            
            # 비밀번호 검증 테스트
            test_passwords = [
                "Admin123!@#",
                "admin123",
                "password",
                "123456",
                "admin",
                "skyboot123"
            ]
            
            print(f"\n🔐 비밀번호 검증 테스트:")
            for password in test_passwords:
                is_valid = AuthService.verify_password(password, admin_user.hashed_password)
                status = "✅ 일치" if is_valid else "❌ 불일치"
                print(f"   - '{password}': {status}")
                if is_valid:
                    print(f"🎉 올바른 비밀번호 발견: {password}")
                    break
        else:
            print("❌ admin@skyboot.com 계정을 찾을 수 없습니다.")
            
            # 모든 사용자 목록 조회
            all_users = db.query(User).limit(10).all()
            print(f"\n📋 등록된 사용자 목록 (최대 10개):")
            for user in all_users:
                print(f"   - {user.email} ({user.username}) - 조직: {user.org_id}")
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    check_admin_account()