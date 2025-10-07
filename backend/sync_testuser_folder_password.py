#!/usr/bin/env python3
"""
testuser_folder 사용자의 User와 MailUser 테이블 패스워드 동기화 스크립트
"""

import sys
import os
from sqlalchemy.orm import Session
import bcrypt

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.user import get_db as get_user_db
from app.database.mail import get_db as get_mail_db
from app.model.user_model import User
from app.model.mail_model import MailUser

def sync_passwords():
    """testuser_folder 사용자의 패스워드를 User와 MailUser 테이블에서 동기화합니다."""
    
    # 사용자 데이터베이스 연결
    user_db_gen = get_user_db()
    user_db: Session = next(user_db_gen)
    
    # 메일 데이터베이스 연결
    mail_db_gen = get_mail_db()
    mail_db: Session = next(mail_db_gen)
    
    try:
        print("🔑 testuser_folder 패스워드 동기화")
        print("=" * 50)
        
        # 새 패스워드 설정
        new_password = "test123"
        
        # 패스워드 해시화
        password_bytes = new_password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt)
        hashed_password_str = hashed_password.decode('utf-8')
        
        # User 테이블에서 사용자 조회 및 업데이트
        user = user_db.query(User).filter(User.user_id == "testuser_folder").first()
        if user:
            user.hashed_password = hashed_password_str
            user_db.commit()
            print(f"✅ User 테이블 패스워드 업데이트 완료")
            print(f"   사용자 ID: {user.user_id}")
            print(f"   이메일: {user.email}")
        else:
            print("❌ User 테이블에서 testuser_folder를 찾을 수 없습니다.")
        
        # MailUser 테이블에서 사용자 조회 및 업데이트
        mail_user = mail_db.query(MailUser).filter(MailUser.email == "testuser_folder@example.com").first()
        if mail_user:
            mail_user.password_hash = hashed_password_str
            mail_db.commit()
            print(f"✅ MailUser 테이블 패스워드 업데이트 완료")
            print(f"   이메일: {mail_user.email}")
            print(f"   표시명: {mail_user.display_name}")
        else:
            print("❌ MailUser 테이블에서 testuser_folder@example.com을 찾을 수 없습니다.")
        
        print(f"\n🔑 새 패스워드: {new_password}")
        
        # 패스워드 검증 테스트
        print(f"\n🧪 패스워드 검증 테스트...")
        test_password = new_password.encode('utf-8')
        
        if user:
            stored_hash = user.hashed_password.encode('utf-8')
            if bcrypt.checkpw(test_password, stored_hash):
                print("✅ User 테이블 패스워드 검증 성공!")
            else:
                print("❌ User 테이블 패스워드 검증 실패!")
        
        if mail_user:
            stored_hash = mail_user.password_hash.encode('utf-8')
            if bcrypt.checkpw(test_password, stored_hash):
                print("✅ MailUser 테이블 패스워드 검증 성공!")
            else:
                print("❌ MailUser 테이블 패스워드 검증 실패!")
            
    except Exception as e:
        print(f"❌ 패스워드 동기화 중 오류: {str(e)}")
        user_db.rollback()
        mail_db.rollback()
    finally:
        user_db.close()
        mail_db.close()

def main():
    """메인 함수"""
    sync_passwords()

if __name__ == "__main__":
    main()