#!/usr/bin/env python3
"""
testuser_folder 사용자 패스워드 재설정 스크립트
"""

import sys
import os
from sqlalchemy.orm import Session
import bcrypt

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.user import get_db
from app.model.user_model import User

def reset_password():
    """testuser_folder 사용자의 패스워드를 재설정합니다."""
    
    # 데이터베이스 연결
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        print("🔑 testuser_folder 패스워드 재설정")
        print("=" * 50)
        
        # 사용자 조회
        user = db.query(User).filter(User.user_id == "testuser_folder").first()
        
        if not user:
            print("❌ testuser_folder 사용자를 찾을 수 없습니다.")
            return
        
        print(f"✅ 사용자 발견: {user.email}")
        
        # 새 패스워드 설정
        new_password = "test123"
        
        # 패스워드 해시화
        password_bytes = new_password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt)
        
        # 패스워드 업데이트
        user.password_hash = hashed_password.decode('utf-8')
        
        db.commit()
        
        print(f"✅ 패스워드 재설정 완료!")
        print(f"   새 패스워드: {new_password}")
        print(f"   사용자 ID: {user.user_id}")
        print(f"   이메일: {user.email}")
        
        # 패스워드 검증 테스트
        print(f"\n🧪 패스워드 검증 테스트...")
        test_password = new_password.encode('utf-8')
        stored_hash = user.password_hash.encode('utf-8')
        
        if bcrypt.checkpw(test_password, stored_hash):
            print("✅ 패스워드 검증 성공!")
        else:
            print("❌ 패스워드 검증 실패!")
            
    except Exception as e:
        print(f"❌ 패스워드 재설정 중 오류: {str(e)}")
        db.rollback()
    finally:
        db.close()

def main():
    """메인 함수"""
    reset_password()

if __name__ == "__main__":
    main()