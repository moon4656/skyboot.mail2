#!/usr/bin/env python3
"""
관리자 사용자 계정 확인
"""

import os
import sys
sys.path.append(os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings

def check_admin_users():
    """관리자 사용자 계정 확인"""
    try:
        # 데이터베이스 연결
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("🔍 관리자 사용자 계정 확인")
        print("=" * 60)
        
        # 모든 사용자 조회 (관리자 역할 포함)
        query = text("""
            SELECT 
                user_id,
                username,
                email,
                role,
                is_active,
                org_id,
                created_at
            FROM users 
            WHERE is_active = true
            ORDER BY role DESC, created_at ASC
        """)
        
        result = db.execute(query)
        users = result.fetchall()
        
        if users:
            print(f"📊 총 {len(users)}명의 활성 사용자 발견:")
            print()
            
            admin_count = 0
            for user in users:
                role_icon = "👑" if user.role == "admin" else "👤"
                print(f"{role_icon} 사용자 ID: {user.user_id}")
                print(f"   사용자명: {user.username}")
                print(f"   이메일: {user.email}")
                print(f"   역할: {user.role}")
                print(f"   조직 ID: {user.org_id}")
                print(f"   생성일: {user.created_at}")
                print()
                
                if user.role == "admin":
                    admin_count += 1
            
            print(f"👑 관리자 계정 수: {admin_count}명")
            
            if admin_count > 0:
                print("\n💡 테스트용 로그인 정보:")
                admin_users = [u for u in users if u.role == "admin"]
                for admin in admin_users[:3]:  # 최대 3명까지만 표시
                    print(f"   user_id: {admin.user_id}")
                    print(f"   password: (데이터베이스에서 해시된 상태로 저장됨)")
                    print()
        else:
            print("❌ 활성 사용자가 없습니다.")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_admin_users()