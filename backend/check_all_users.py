#!/usr/bin/env python3
"""
모든 사용자 계정 목록을 확인하는 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.model.user_model import User
from app.model.mail_model import MailUser
from app.model.organization_model import Organization

def main():
    print("🔍 전체 사용자 계정 목록 확인")
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as db:
        print("\n📋 1. 전체 사용자 목록")
        users = db.query(User).all()
        print(f"총 사용자 수: {len(users)}명")
        
        for user in users:
            print(f"   - ID: {user.user_id}, UUID: {user.user_uuid}")
            print(f"     이메일: {user.email}")
            print(f"     사용자명: {user.username}")
            print(f"     조직 ID: {user.org_id}")
            print(f"     활성화: {user.is_active}")
            print(f"     생성일: {user.created_at}")
            print()
        
        print("\n📋 2. 메일 사용자 목록")
        mail_users = db.query(MailUser).all()
        print(f"총 메일 사용자 수: {len(mail_users)}명")
        
        for mail_user in mail_users:
            print(f"   - ID: {mail_user.user_id}, UUID: {mail_user.user_uuid}")
            print(f"     이메일: {mail_user.email}")
            print(f"     조직 ID: {mail_user.org_id}")
            print(f"     활성화: {mail_user.is_active}")
            print(f"     생성일: {mail_user.created_at}")
            print()
        
        print("\n📋 3. 조직 목록")
        organizations = db.query(Organization).all()
        print(f"총 조직 수: {len(organizations)}개")
        
        for org in organizations:
            print(f"   - ID: {org.id}, UUID: {org.org_uuid}")
            print(f"     조직명: {org.name}")
            print(f"     도메인: {org.domain}")
            print(f"     활성화: {org.is_active}")
            print()
        
        print("\n📋 4. 최근 로그인 기록 확인")
        # 최근 로그인 기록이 있는 사용자 확인
        recent_login_query = text("""
            SELECT DISTINCT u.email, u.username, u.user_uuid, u.org_id
            FROM users u
            WHERE u.last_login_at IS NOT NULL
            ORDER BY u.last_login_at DESC
            LIMIT 10
        """)
        recent_logins = db.execute(recent_login_query).fetchall()
        
        print(f"최근 로그인한 사용자: {len(recent_logins)}명")
        for login in recent_logins:
            print(f"   - {login.email} ({login.username})")
            print(f"     UUID: {login.user_uuid}, 조직: {login.org_id}")

if __name__ == "__main__":
    main()