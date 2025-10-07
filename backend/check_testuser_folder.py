#!/usr/bin/env python3
"""
testuser_folder 사용자 정보 확인 스크립트
"""

import sys
import os
from sqlalchemy.orm import Session

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.user import get_db
from app.model.user_model import User
from app.model.mail_model import MailUser

def check_testuser_folder():
    """testuser_folder 사용자 정보를 확인합니다."""
    
    # 데이터베이스 연결
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        print("🔍 testuser_folder 사용자 정보 확인")
        print("=" * 60)
        
        # 1. MailUser 테이블에서 검색
        print("1️⃣ MailUser 테이블에서 검색...")
        mail_user = db.query(MailUser).filter(
            MailUser.email == "testuser_folder@example.com"
        ).first()
        
        if mail_user:
            print(f"✅ MailUser 발견!")
            print(f"   - 이메일: {mail_user.email}")
            print(f"   - 사용자 UUID: {mail_user.user_uuid}")
            print(f"   - 표시 이름: {mail_user.display_name}")
            print(f"   - 조직 ID: {mail_user.org_id}")
            print(f"   - 활성 상태: {mail_user.is_active}")
            
            # 2. User 테이블에서 해당 UUID로 검색
            print("\n2️⃣ User 테이블에서 해당 UUID로 검색...")
            user = db.query(User).filter(
                User.user_uuid == mail_user.user_uuid
            ).first()
            
            if user:
                print(f"✅ User 발견!")
                print(f"   - 사용자 ID: {user.user_id}")
                print(f"   - 이메일: {user.email}")
                print(f"   - 사용자명: {user.username}")
                print(f"   - 조직 ID: {user.org_id}")
                print(f"   - 활성 상태: {user.is_active}")
                print(f"   - 역할: {user.role}")
                print(f"   - 생성 시간: {user.created_at}")
            else:
                print("❌ User 테이블에서 해당 UUID를 찾을 수 없습니다.")
                
                # 3. 이메일로 User 테이블 검색
                print("\n3️⃣ 이메일로 User 테이블 검색...")
                user_by_email = db.query(User).filter(
                    User.email == "testuser_folder@example.com"
                ).first()
                
                if user_by_email:
                    print(f"✅ 이메일로 User 발견!")
                    print(f"   - 사용자 ID: {user_by_email.user_id}")
                    print(f"   - 사용자 UUID: {user_by_email.user_uuid}")
                    print(f"   - 이메일: {user_by_email.email}")
                    print(f"   - 사용자명: {user_by_email.username}")
                    print(f"   - 조직 ID: {user_by_email.org_id}")
                    print(f"   - 활성 상태: {user_by_email.is_active}")
                else:
                    print("❌ 이메일로도 User를 찾을 수 없습니다.")
        else:
            print("❌ MailUser 테이블에서 testuser_folder@example.com을 찾을 수 없습니다.")
        
        # 4. 모든 User 목록 확인
        print("\n4️⃣ 전체 User 목록 (최근 10개)...")
        users = db.query(User).order_by(User.created_at.desc()).limit(10).all()
        
        for user in users:
            print(f"   - ID: {user.user_id} | 이메일: {user.email} | UUID: {user.user_uuid}")
            
    except Exception as e:
        print(f"❌ 사용자 조회 중 오류: {str(e)}")
    finally:
        db.close()

def main():
    """메인 함수"""
    check_testuser_folder()

if __name__ == "__main__":
    main()