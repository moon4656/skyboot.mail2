#!/usr/bin/env python3
"""
테스트용 사용자 정보 확인 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database.user import get_db
from app.model.user_model import User
from app.service.auth_service import verify_password

def check_users():
    """사용자 정보 확인"""
    db = next(get_db())
    
    try:
        # 모든 사용자 조회
        users = db.query(User).all()
        
        print("=== 등록된 사용자 목록 ===")
        for user in users:
            print(f"User ID: {user.user_id}")
            print(f"User UUID: {user.user_uuid}")
            print(f"Email: {user.email}")
            print(f"Username: {user.username}")
            print(f"Active: {user.is_active}")
            print(f"Created: {user.created_at}")
            print("---")
        
        # user01 사용자 확인
        user01 = db.query(User).filter(User.user_id == "user01").first()
        if user01:
            print(f"\n=== user01 정보 ===")
            print(f"User ID: {user01.user_id}")
            print(f"User UUID: {user01.user_uuid}")
            print(f"Email: {user01.email}")
            print(f"Username: {user01.username}")
            print(f"Active: {user01.is_active}")
            print(f"Password Hash: {user01.hashed_password[:20]}...")
            
            # 비밀번호 확인
            password_check1 = verify_password("password123", user01.hashed_password)
            password_check2 = verify_password("test", user01.hashed_password)
            print(f"Password 'password123' 검증: {password_check1}")
            print(f"Password 'test' 검증: {password_check2}")
            
        else:
            print("\n❌ user01 사용자를 찾을 수 없습니다.")
            
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_users()