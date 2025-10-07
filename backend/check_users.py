#!/usr/bin/env python3
"""
데이터베이스 사용자 목록 확인 스크립트
"""

import sys
import os
from sqlalchemy.orm import Session

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.user import get_db
from app.model.user_model import User
from app.model.mail_model import MailUser

def check_users():
    """데이터베이스에서 사용자 목록을 확인합니다."""
    
    # 데이터베이스 연결
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        print("👥 User 테이블 사용자 목록:")
        print("=" * 60)
        
        users = db.query(User).all()
        
        if users:
            for user in users:
                print(f"🔹 사용자 ID: {user.user_id}")
                print(f"   - 이메일: {user.email}")
                print(f"   - 사용자명: {user.username}")
                print(f"   - 조직 ID: {user.org_id}")
                print(f"   - 활성 상태: {user.is_active}")
                print(f"   - 역할: {user.role}")
                print()
        else:
            print("❌ User 테이블에 사용자가 없습니다.")
        
        print("\n📧 MailUser 테이블 사용자 목록:")
        print("=" * 60)
        
        mail_users = db.query(MailUser).all()
        
        if mail_users:
            for mail_user in mail_users:
                print(f"🔹 메일 사용자 UUID: {mail_user.user_uuid}")
                print(f"   - 이메일: {mail_user.email}")
                print(f"   - 표시 이름: {mail_user.display_name}")
                print(f"   - 조직 ID: {mail_user.org_id}")
                print(f"   - 활성 상태: {mail_user.is_active}")
                print()
        else:
            print("❌ MailUser 테이블에 사용자가 없습니다.")
            
    except Exception as e:
        print(f"❌ 사용자 조회 중 오류: {str(e)}")
    finally:
        db.close()

def main():
    """메인 함수"""
    print("🔍 데이터베이스 사용자 확인")
    print("=" * 60)
    
    check_users()

if __name__ == "__main__":
    main()