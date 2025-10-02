#!/usr/bin/env python3
"""
사용자의 실제 org_id 값을 확인하는 디버그 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.model import User, Organization

def check_user_org_id():
    """사용자의 org_id 값을 확인합니다."""
    
    print("🔍 사용자 org_id 디버그 시작...")
    
    db = next(get_db())
    
    try:
        # 테스트 사용자 조회
        test_email = "user02@example.com"
        user = db.query(User).filter(User.email == test_email).first()
        
        if user:
            print(f"✅ 사용자 발견: {user.email}")
            print(f"   - user_id: {user.user_id}")
            print(f"   - user_uuid: {user.user_uuid}")
            print(f"   - org_id: {user.org_id}")
            print(f"   - org_id 타입: {type(user.org_id)}")
            print(f"   - username: {user.username}")
            print(f"   - role: {user.role}")
            print(f"   - is_active: {user.is_active}")
            
            # 해당 조직 정보 조회
            org = db.query(Organization).filter(Organization.org_id == user.org_id).first()
            if org:
                print(f"✅ 연결된 조직 발견: {org.name}")
                print(f"   - org_id: {org.org_id}")
                print(f"   - org_code: {org.org_code}")
                print(f"   - is_active: {org.is_active}")
            else:
                print(f"❌ 연결된 조직을 찾을 수 없음: {user.org_id}")
                
                # 모든 조직 목록 출력
                print("\n📋 전체 조직 목록:")
                all_orgs = db.query(Organization).all()
                for org in all_orgs:
                    print(f"   - {org.name}: {org.org_id} (활성: {org.is_active})")
        else:
            print(f"❌ 사용자를 찾을 수 없음: {test_email}")
            
            # 모든 사용자 목록 출력
            print("\n📋 전체 사용자 목록:")
            all_users = db.query(User).all()
            for user in all_users:
                print(f"   - {user.email}: org_id={user.org_id}")
                
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_user_org_id()