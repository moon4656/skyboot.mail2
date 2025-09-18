#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
사용자 데이터베이스 확인 스크립트
"""

from sqlalchemy.orm import Session
from app.database.base import get_db
from app.model.base_model import User
from app.service.auth_service import verify_password, get_password_hash

def check_user():
    """테스트 사용자 정보를 확인합니다"""
    db = next(get_db())
    
    try:
        # 테스트 사용자 조회
        test_email = "test@skyboot.com"
        user = db.query(User).filter(User.email == test_email).first()
        
        if user:
            print(f"✅ 사용자 발견:")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Username: {user.username}")
            print(f"   Is Active: {user.is_active}")
            print(f"   Created At: {user.created_at}")
            print(f"   Hashed Password: {user.hashed_password[:50]}...")
            
            # 비밀번호 검증 테스트
            test_password = "test123456"
            is_valid = verify_password(test_password, user.hashed_password)
            print(f"   Password Valid: {is_valid}")
            
            if not is_valid:
                print("\n🔧 비밀번호 재설정 시도...")
                new_hash = get_password_hash(test_password)
                user.hashed_password = new_hash
                db.commit()
                print("✅ 비밀번호가 재설정되었습니다.")
                
                # 재검증
                is_valid_after = verify_password(test_password, user.hashed_password)
                print(f"   Password Valid After Reset: {is_valid_after}")
        else:
            print(f"❌ 사용자를 찾을 수 없습니다: {test_email}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    check_user()