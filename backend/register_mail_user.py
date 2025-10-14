#!/usr/bin/env python3
"""
testadmin 사용자를 MailUser 테이블에 등록하는 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database.user import get_db
from app.model.user_model import User
from app.model.mail_model import MailUser
import uuid

def register_mail_user():
    """testadmin 사용자를 MailUser 테이블에 등록"""
    
    # 데이터베이스 세션 생성
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        print("🔍 testadmin 사용자 조회 중...")
        
        # testadmin 사용자 조회
        user = db.query(User).filter(User.user_id == "testadmin").first()
        if not user:
            print("❌ testadmin 사용자를 찾을 수 없습니다.")
            return False
        
        print(f"✅ testadmin 사용자 찾음:")
        print(f"   - user_uuid: {user.user_uuid}")
        print(f"   - email: {user.email}")
        print(f"   - org_id: {user.org_id}")
        
        # 이미 MailUser에 등록되어 있는지 확인
        existing_mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == user.user_uuid,
            MailUser.org_id == user.org_id
        ).first()
        
        if existing_mail_user:
            print("✅ testadmin 사용자가 이미 MailUser 테이블에 등록되어 있습니다.")
            print(f"   - user_id: {existing_mail_user.user_id}")
            print(f"   - email: {existing_mail_user.email}")
            return True
        
        # MailUser 테이블에 등록
        print("📝 MailUser 테이블에 등록 중...")
        
        mail_user = MailUser(
            user_id=user.user_id,
            user_uuid=user.user_uuid,
            email=user.email,
            password_hash=user.hashed_password,
            is_active=user.is_active,
            org_id=user.org_id,
            created_at=user.created_at
        )
        
        db.add(mail_user)
        db.commit()
        
        print("✅ testadmin 사용자가 MailUser 테이블에 성공적으로 등록되었습니다!")
        print(f"   - user_id: {mail_user.user_id}")
        print(f"   - user_uuid: {mail_user.user_uuid}")
        print(f"   - email: {mail_user.email}")
        print(f"   - org_id: {mail_user.org_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=== testadmin 사용자 MailUser 등록 스크립트 ===")
    success = register_mail_user()
    if success:
        print("\n🎉 등록 완료!")
    else:
        print("\n💥 등록 실패!")