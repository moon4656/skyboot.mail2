#!/usr/bin/env python3
"""
사용자 확인 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.model.user_model import User
from app.model.organization_model import Organization

def check_users():
    """사용자 목록 확인"""
    
    # 데이터베이스 연결
    engine = create_engine(settings.get_database_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 모든 사용자 조회 (조직 정보와 함께)
        users = db.query(User).join(Organization).all()
        
        print(f"👥 총 {len(users)}명의 사용자가 있습니다:")
        print()
        
        for user in users:
            print(f"👤 사용자: {user.username} ({user.email})")
            print(f"   - user_id: {user.user_id}")
            print(f"   - user_uuid: {user.user_uuid}")
            print(f"   - org_id: {user.org_id}")
            print(f"   - 조직: {user.organization.name if user.organization else 'N/A'}")
            print(f"   - role: {user.role}")
            print(f"   - is_active: {user.is_active}")
            print(f"   - created_at: {user.created_at}")
            print()
        
        if not users:
            print("⚠️ 사용자가 없습니다.")
            
        # admin01 사용자 특별 확인
        admin01 = db.query(User).filter(User.user_id == "admin01").first()
        if admin01:
            print("🔍 admin01 사용자 상세 정보:")
            print(f"   - email: {admin01.email}")
            print(f"   - org_id: {admin01.org_id}")
            print(f"   - 조직: {admin01.organization.name if admin01.organization else 'N/A'}")
            print(f"   - is_active: {admin01.is_active}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_users()