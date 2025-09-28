#!/usr/bin/env python3
"""
MailUser 이메일 간단 수정 스크립트
===============================

올바른 MailUser의 이메일을 수정합니다.
"""

import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from app.database.user import engine
from app.model.user_model import User
from app.model.mail_model import MailUser

def simple_fix_mail_user():
    """
    올바른 MailUser의 이메일을 수정합니다.
    """
    # 데이터베이스 세션 생성
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("🔍 올바른 User 조회...")
        
        # mailtest@skyboot.com 사용자 조회
        user = db.query(User).filter(User.email == "mailtest@skyboot.com").first()
        
        if not user:
            print("❌ mailtest@skyboot.com 사용자를 찾을 수 없습니다.")
            return
        
        print(f"✅ User 발견:")
        print(f"   - user_id: {user.user_id}")
        print(f"   - email: {user.email}")
        
        # 해당 User에 대응하는 MailUser 조회
        mail_user = db.query(MailUser).filter(
            MailUser.user_id == user.user_id,
            MailUser.org_id == user.org_id
        ).first()
        
        if not mail_user:
            print("❌ 해당 사용자의 MailUser를 찾을 수 없습니다.")
            return
        
        print(f"\n📧 현재 MailUser:")
        print(f"   - user_uuid: {mail_user.user_uuid}")
        print(f"   - email: {mail_user.email}")
        
        # 고아 MailUser를 임시로 다른 이메일로 변경
        print(f"\n🔍 고아 MailUser 임시 변경...")
        orphan_mail_user = db.query(MailUser).filter(
            MailUser.email == "mailtest@skyboot.com"
        ).first()
        
        if orphan_mail_user and orphan_mail_user.user_uuid != mail_user.user_uuid:
            print(f"🔧 고아 MailUser 이메일 임시 변경...")
            orphan_mail_user.email = "temp_mailtest@skyboot.com"
            db.commit()
            print("✅ 고아 MailUser 임시 변경 완료")
        
        # 이제 올바른 MailUser의 이메일 수정
        print(f"\n🔧 올바른 MailUser 이메일 수정...")
        mail_user.email = user.email
        db.commit()
        
        print("✅ MailUser 이메일 수정 완료")
        
        # 최종 확인
        print(f"\n📧 최종 MailUser 상태:")
        print(f"   - user_uuid: {mail_user.user_uuid}")
        print(f"   - email: {mail_user.email}")
        print(f"   - display_name: {mail_user.display_name}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        db.rollback()
        
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 MailUser 이메일 간단 수정 스크립트 시작")
    print("=" * 50)
    
    simple_fix_mail_user()
    
    print("=" * 50)