#!/usr/bin/env python3
"""
moonsoo 사용자의 패스워드 해시 확인 스크립트
"""
import asyncio
import asyncpg
from passlib.context import CryptContext
from app.config import settings

# 패스워드 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def verify_password():
    """패스워드 해시 확인"""
    try:
        # 데이터베이스 연결
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME
        )
        
        print("🔍 moonsoo 사용자 패스워드 해시 확인...")
        
        # moonsoo 사용자 조회
        user = await conn.fetchrow("""
            SELECT user_id, username, email, hashed_password, is_active, org_id
            FROM users 
            WHERE user_id = 'moonsoo'
        """)
        
        if not user:
            print("❌ moonsoo 사용자를 찾을 수 없습니다.")
            return
        
        print(f"✅ 사용자 발견:")
        print(f"   user_id: {user['user_id']}")
        print(f"   username: {user['username']}")
        print(f"   email: {user['email']}")
        print(f"   is_active: {user['is_active']}")
        print(f"   org_id: {user['org_id']}")
        print(f"   hashed_password: {user['hashed_password'][:50]}...")
        
        # 패스워드 검증
        test_passwords = ["safe70!!", "password", "123456", "admin"]
        
        print(f"\n🔐 패스워드 검증 테스트:")
        for password in test_passwords:
            is_valid = pwd_context.verify(password, user['hashed_password'])
            status = "✅ 일치" if is_valid else "❌ 불일치"
            print(f"   '{password}': {status}")
        
        # 새로운 패스워드 해시 생성 (참고용)
        new_hash = pwd_context.hash("safe70!!")
        print(f"\n🔧 'safe70!!' 새 해시 (참고용): {new_hash}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_password())