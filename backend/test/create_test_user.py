#!/usr/bin/env python3
"""
테스트용 사용자 생성 스크립트
"""

import sys
import os
from datetime import datetime
from sqlalchemy.orm import Session

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.user import get_db
from app.model.user_model import User
from app.model.organization_model import Organization
from app.service.auth_service import get_password_hash

def create_test_users():
    """테스트용 사용자들을 생성합니다."""
    
    print("🔧 테스트용 사용자 생성 시작...")
    
    db = next(get_db())
    
    try:
        # 테스트 조직 생성 또는 확인
        test_org_id = "test-org-001"
        existing_org = db.query(Organization).filter(Organization.org_id == test_org_id).first()
        
        if not existing_org:
            test_org = Organization(
                org_id=test_org_id,
                org_code="testorg001",
                name="테스트 조직",
                domain="test.example.com",
                subdomain="testorg",
                admin_email="admin@test.example.com",
                max_users=100,
                is_active=True
            )
            db.add(test_org)
            db.commit()
            print(f"✅ 테스트 조직 {test_org_id}를 생성했습니다.")
        else:
            print(f"✅ 테스트 조직 {test_org_id}는 이미 존재합니다.")
        
        test_users = [
            {
                "user_id": "testuser1",
                "email": "testuser1@example.com",
                "username": "testuser1",
                "password": "testpassword123"
            },
            {
                "user_id": "testuser2",
                "email": "testuser2@example.com", 
                "username": "testuser2",
                "password": "testpassword123"
            }
        ]
        
        for user_data in test_users:
            # 기존 사용자 확인
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            
            if existing_user:
                print(f"✅ 사용자 {user_data['email']}는 이미 존재합니다.")
                # 비밀번호 업데이트
                existing_user.hashed_password = get_password_hash(user_data["password"])
                db.commit()
                print(f"🔑 사용자 {user_data['email']}의 비밀번호를 업데이트했습니다.")
            else:
                # 새 사용자 생성
                new_user = User(
                    user_id=user_data["user_id"],
                    org_id=test_org_id,
                    email=user_data["email"],
                    username=user_data["username"],
                    hashed_password=get_password_hash(user_data["password"]),
                    is_active=True
                )
                
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                
                print(f"✅ 새 사용자 {user_data['email']}를 생성했습니다.")
        
        print("\n📋 테스트 사용자 정보:")
        print("=" * 50)
        for user_data in test_users:
            print(f"📧 이메일: {user_data['email']}")
            print(f"🔑 비밀번호: {user_data['password']}")
            print("-" * 30)
        
    except Exception as e:
        db.rollback()
        print(f"❌ 사용자 생성 중 오류: {str(e)}")
        raise
    
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users()