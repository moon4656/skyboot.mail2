#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터베이스 사용자 목록 확인 스크립트
"""

from sqlalchemy.orm import Session
from app.database.base import get_db
from app.model.base_model import User

def list_all_users():
    """데이터베이스의 모든 사용자를 조회합니다"""
    db = next(get_db())
    
    try:
        # 모든 사용자 조회
        users = db.query(User).all()
        
        print(f"📊 총 사용자 수: {len(users)}")
        print("=" * 80)
        
        if users:
            for i, user in enumerate(users, 1):
                print(f"👤 사용자 #{i}:")
                print(f"   ID: {user.id}")
                print(f"   Email: {user.email}")
                print(f"   Username: {user.username}")
                print(f"   Is Active: {user.is_active}")
                print(f"   Created At: {user.created_at}")
                print(f"   Hashed Password: {user.hashed_password[:50]}...")
                print("-" * 40)
        else:
            print("❌ 등록된 사용자가 없습니다.")
            
        # 특정 이메일과 사용자명 검색
        test_email = "test@skyboot.com"
        test_username = "testuser"
        
        print(f"\n🔍 특정 검색 결과:")
        
        user_by_email = db.query(User).filter(User.email == test_email).first()
        if user_by_email:
            print(f"✅ 이메일 '{test_email}'로 사용자 발견: {user_by_email.username}")
        else:
            print(f"❌ 이메일 '{test_email}'로 사용자를 찾을 수 없음")
            
        user_by_username = db.query(User).filter(User.username == test_username).first()
        if user_by_username:
            print(f"✅ 사용자명 '{test_username}'로 사용자 발견: {user_by_username.email}")
        else:
            print(f"❌ 사용자명 '{test_username}'로 사용자를 찾을 수 없음")
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 80)
    print("📋 데이터베이스 사용자 목록")
    print("=" * 80)
    list_all_users()