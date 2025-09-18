#!/usr/bin/env python3
"""
User 테이블의 user_uuid 컬럼 문제 해결
"""

import uuid
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.base import engine, SessionLocal
from app.model.base_model import User
from sqlalchemy import text

def fix_user_uuid_column():
    """user_uuid 컬럼 문제 해결"""
    print("🔧 User 테이블의 user_uuid 컬럼 문제 해결 중...")
    
    with engine.connect() as conn:
        try:
            # 1. 현재 테이블 구조 확인
            print("1. 현재 users 테이블 구조 확인...")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position;
            """))
            columns = result.fetchall()
            
            print("현재 컬럼:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            
            # 2. user_uuid 컬럼이 있는지 확인
            column_names = [col[0] for col in columns]
            
            if 'user_uuid' not in column_names:
                print("2. user_uuid 컬럼 추가...")
                conn.execute(text('ALTER TABLE users ADD COLUMN user_uuid VARCHAR(36) UNIQUE;'))
                conn.commit()
                print("✅ user_uuid 컬럼이 추가되었습니다.")
            else:
                print("2. user_uuid 컬럼이 이미 존재합니다.")
            
            # 3. 기존 사용자들에게 UUID 할당
            print("3. 기존 사용자들에게 UUID 할당...")
            
            # NULL인 user_uuid를 가진 사용자들 조회
            result = conn.execute(text("SELECT id FROM users WHERE user_uuid IS NULL;"))
            users_without_uuid = result.fetchall()
            
            if users_without_uuid:
                print(f"UUID가 없는 사용자 수: {len(users_without_uuid)}")
                
                for user_row in users_without_uuid:
                    user_id = user_row[0]
                    new_uuid = str(uuid.uuid4())
                    conn.execute(text(
                        "UPDATE users SET user_uuid = :uuid WHERE id = :user_id"
                    ), {'uuid': new_uuid, 'user_id': user_id})
                    print(f"  사용자 ID {user_id}에게 UUID {new_uuid} 할당")
                
                conn.commit()
                print("✅ 모든 사용자에게 UUID가 할당되었습니다.")
            else:
                print("모든 사용자가 이미 UUID를 가지고 있습니다.")
            
            # 4. 최종 확인
            print("4. 최종 확인...")
            result = conn.execute(text("SELECT id, user_uuid, email FROM users;"))
            users = result.fetchall()
            
            print(f"총 사용자 수: {len(users)}")
            for user in users:
                print(f"  ID: {user[0]}, UUID: {user[1]}, Email: {user[2]}")
            
            print("✅ user_uuid 컬럼 문제가 해결되었습니다!")
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            conn.rollback()
            raise

def create_test_user():
    """테스트용 사용자 생성"""
    print("\n👤 테스트용 사용자 생성...")
    
    db = SessionLocal()
    try:
        # 기존 테스트 사용자 확인
        existing_user = db.query(User).filter(User.email == "test@example.com").first()
        
        if existing_user:
            print("테스트 사용자가 이미 존재합니다.")
            print(f"  ID: {existing_user.id}")
            print(f"  UUID: {existing_user.user_uuid}")
            print(f"  Email: {existing_user.email}")
            return existing_user
        
        # 새 테스트 사용자 생성
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        test_user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=pwd_context.hash("testpassword123"),
            is_active=True
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print("✅ 테스트 사용자가 생성되었습니다.")
        print(f"  ID: {test_user.id}")
        print(f"  UUID: {test_user.user_uuid}")
        print(f"  Email: {test_user.email}")
        
        return test_user
        
    except Exception as e:
        print(f"❌ 테스트 사용자 생성 중 오류: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    try:
        fix_user_uuid_column()
        create_test_user()
        print("\n🎉 모든 작업이 완료되었습니다!")
    except Exception as e:
        print(f"\n💥 실행 중 오류 발생: {e}")
        sys.exit(1)