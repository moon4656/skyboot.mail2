#!/usr/bin/env python3
"""
user01 사용자 정보 확인 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.user import get_db_session
from app.model.user_model import User
from app.model.mail_model import MailUser

def check_user01():
    """user01 사용자 정보를 확인합니다."""
    
    try:
        # 데이터베이스 연결
        with get_db_session() as db:
            
            print("🔍 user01 사용자 정보 확인 중...")
            print("=" * 60)
            
            # User 테이블에서 user01 검색
            users = db.query(User).filter(
                (User.user_id == "user01") | 
                (User.email == "user01@example.com") |
                (User.username == "user01")
            ).all()
            
            if users:
                print(f"✅ User 테이블에서 {len(users)}개의 user01 관련 사용자 발견:")
                for i, user in enumerate(users, 1):
                    print(f"\n📋 사용자 {i}:")
                    print(f"  - user_id: {user.user_id}")
                    print(f"  - user_uuid: {user.user_uuid}")
                    print(f"  - email: {user.email}")
                    print(f"  - username: {user.username}")
                    print(f"  - org_id: {user.org_id}")
                    print(f"  - role: {user.role}")
                    print(f"  - is_active: {user.is_active}")
                    print(f"  - is_email_verified: {user.is_email_verified}")
                    print(f"  - last_login_at: {user.last_login_at}")
                    print(f"  - created_at: {user.created_at}")
            else:
                print("❌ User 테이블에서 user01 관련 사용자를 찾을 수 없습니다.")
            
            # MailUser 테이블에서 user01 검색
            print("\n" + "=" * 60)
            mail_users = db.query(MailUser).filter(
                (MailUser.user_id.like("%user01%")) | 
                (MailUser.email == "user01@example.com")
            ).all()
            
            if mail_users:
                print(f"✅ MailUser 테이블에서 {len(mail_users)}개의 user01 관련 메일 사용자 발견:")
                for i, mail_user in enumerate(mail_users, 1):
                    print(f"\n📧 메일 사용자 {i}:")
                    print(f"  - user_id: {mail_user.user_id}")
                    print(f"  - user_uuid: {mail_user.user_uuid}")
                    print(f"  - email: {mail_user.email}")
                    print(f"  - org_id: {mail_user.org_id}")
                    print(f"  - is_active: {mail_user.is_active}")
                    print(f"  - created_at: {mail_user.created_at}")
            else:
                print("❌ MailUser 테이블에서 user01 관련 메일 사용자를 찾을 수 없습니다.")
            
            # user01의 조직 정보 확인
            print("\n" + "=" * 60)
            print("🏢 user01의 조직 정보 확인 중...")
            
            if users:
                user01 = users[0]  # 첫 번째 user01 사용자
                org = db.query(Organization).filter(Organization.org_id == user01.org_id).first()
                
                if org:
                    print(f"✅ 조직 정보 발견:")
                    print(f"  - org_id: {org.org_id}")
                    print(f"  - org_code: {org.org_code}")
                    print(f"  - name: {org.name}")
                    print(f"  - display_name: {org.display_name}")
                    print(f"  - domain: {org.domain}")
                    print(f"  - subdomain: {org.subdomain}")
                    print(f"  - admin_email: {org.admin_email}")
                    print(f"  - status: {org.status}")
                    print(f"  - is_active: {org.is_active}")
                    print(f"  - max_users: {org.max_users}")
                    print(f"  - created_at: {org.created_at}")
                    
                    if not org.is_active:
                        print("⚠️  경고: 조직이 비활성화 상태입니다! 이것이 로그인 실패의 원인일 수 있습니다.")
                    else:
                        print("✅ 조직이 활성화 상태입니다.")
                else:
                    print(f"❌ 조직을 찾을 수 없습니다. org_id: {user01.org_id}")
            
            # 전체 사용자 수 확인
            print("\n" + "=" * 60)
            total_users = db.query(User).count()
            total_mail_users = db.query(MailUser).count()
            print(f"📊 전체 통계:")
            print(f"  - 총 User 수: {total_users}")
            print(f"  - 총 MailUser 수: {total_mail_users}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_user01()