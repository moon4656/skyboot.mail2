#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
테스트용 사용자 생성 및 확인 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash, verify_password
from datetime import datetime, timezone

def create_test_user():
    """테스트용 사용자 생성"""
    db = SessionLocal()
    try:
        # 기존 사용자 확인
        existing_user = db.query(User).filter(User.email == "test@example.com").first()
        if existing_user:
            print(f"기존 사용자 발견: {existing_user.email}")
            return existing_user
        
        # 새 사용자 생성
        hashed_password = get_password_hash("test123")
        new_user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hashed_password,
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"새 사용자 생성: {new_user.email}")
        return new_user
        
    except Exception as e:
        print(f"사용자 생성 오류: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def list_users():
    """모든 사용자 목록 조회"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"\n총 {len(users)}명의 사용자:")
        for user in users:
            print(f"- {user.email} (활성: {user.is_active})")
        return users
    except Exception as e:
        print(f"사용자 조회 오류: {e}")
        return []
    finally:
        db.close()

if __name__ == "__main__":
    print("=== 메일 사용자 관리 ===")
    
    # 기존 사용자 목록 조회
    list_users()
    
    # 테스트 사용자 생성
    test_user = create_test_user()
    
    # 업데이트된 사용자 목록 조회
    list_users()
    
    if test_user:
        print(f"\n테스트 로그인 정보:")
        print(f"이메일: test@example.com")
        print(f"비밀번호: test123")