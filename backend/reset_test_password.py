#!/usr/bin/env python3
"""
테스트 사용자의 비밀번호를 재설정하는 스크립트
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from app.database.user import engine
from app.model.user_model import User
from app.service.auth_service import AuthService

def reset_test_password():
    """테스트 사용자의 비밀번호를 재설정합니다."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 테스트 사용자 찾기
        user = db.query(User).filter(User.email == "test@skyboot.com").first()
        
        if not user:
            print("❌ 테스트 사용자를 찾을 수 없습니다.")
            return
        
        print(f"👤 사용자 발견: {user.email}")
        print(f"현재 해시된 비밀번호: {user.hashed_password}")
        
        # 새 비밀번호 해시 생성
        new_password = "testpassword123"
        new_hash = AuthService.get_password_hash(new_password)
        
        print(f"새 해시된 비밀번호: {new_hash}")
        
        # 비밀번호 업데이트
        user.hashed_password = new_hash
        db.commit()
        
        print("✅ 비밀번호 업데이트 완료")
        
        # 검증
        is_valid = AuthService.verify_password(new_password, user.hashed_password)
        print(f"🔐 비밀번호 검증 결과: {'✅ 성공' if is_valid else '❌ 실패'}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_test_password()