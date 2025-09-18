#!/usr/bin/env python3
"""
User와 MailUser를 동기화하는 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.base import SessionLocal
from app.model.base_model import User
from app.model.mail_model import MailUser
import hashlib

def sync_users():
    """User와 MailUser 동기화"""
    print("🔄 User와 MailUser 동기화 중...")
    
    db = SessionLocal()
    try:
        # 1. 모든 User 조회
        users = db.query(User).all()
        print(f"총 {len(users)}개의 User 발견")
        
        for user in users:
            print(f"  User: {user.email} (ID: {user.id})")
            
            # 해당 이메일의 MailUser 찾기
            mail_user = db.query(MailUser).filter(MailUser.email == user.email).first()
            
            if mail_user:
                # 기존 MailUser 업데이트
                if mail_user.user_id != user.id:
                    mail_user.user_id = user.id
                    print(f"    ✅ 기존 MailUser 업데이트: user_id = {user.id}")
                else:
                    print(f"    ℹ️ 이미 연결됨")
            else:
                # 새 MailUser 생성
                mail_user = MailUser(
                    user_id=user.id,
                    email=user.email,
                    password_hash=user.hashed_password,
                    display_name=user.username,
                    is_active=user.is_active
                )
                db.add(mail_user)
                print(f"    ✅ 새 MailUser 생성")
        
        # 2. 테스트용 사용자 확인
        test_email = "test@example.com"
        test_user = db.query(User).filter(User.email == test_email).first()
        
        if test_user:
            print(f"\n📧 테스트 사용자 확인: {test_email}")
            mail_user = db.query(MailUser).filter(MailUser.email == test_email).first()
            if mail_user and mail_user.user_id != test_user.id:
                mail_user.user_id = test_user.id
                print(f"  ✅ 테스트 MailUser 연결: user_id = {test_user.id}")
        
        db.commit()
        
        # 3. 최종 확인
        print("\n📊 최종 상태:")
        mail_users = db.query(MailUser).all()
        for mail_user in mail_users:
            user_info = f"연결됨 (User ID: {mail_user.user_id})" if mail_user.user_id else "연결 안됨"
            print(f"  MailUser: {mail_user.email} - {user_info}")
        
        print("✅ User와 MailUser 동기화 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    sync_users()