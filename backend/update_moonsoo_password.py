#!/usr/bin/env python3
"""
moonsoo 사용자의 패스워드를 'safe70!!'로 업데이트하는 스크립트
"""
import asyncio
import asyncpg
from passlib.context import CryptContext
from app.config import settings

# 패스워드 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def update_password():
    """패스워드 업데이트"""
    try:
        # 데이터베이스 연결
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME
        )
        
        print("🔐 moonsoo 사용자 패스워드 업데이트...")
        
        # 새 패스워드 해시 생성
        new_password = "safe70!!"
        new_hash = pwd_context.hash(new_password)
        
        print(f"새 패스워드: {new_password}")
        print(f"새 해시: {new_hash}")
        
        # 기존 사용자 확인
        user = await conn.fetchrow("""
            SELECT user_id, username, email, hashed_password
            FROM users 
            WHERE user_id = 'moonsoo'
        """)
        
        if not user:
            print("❌ moonsoo 사용자를 찾을 수 없습니다.")
            return
        
        print(f"✅ 기존 사용자 발견: {user['user_id']}")
        print(f"   기존 해시: {user['hashed_password'][:50]}...")
        
        # 패스워드 업데이트
        result = await conn.execute("""
            UPDATE users 
            SET hashed_password = $1, updated_at = NOW()
            WHERE user_id = 'moonsoo'
        """, new_hash)
        
        print(f"✅ 패스워드 업데이트 완료: {result}")
        
        # 업데이트 확인
        updated_user = await conn.fetchrow("""
            SELECT user_id, hashed_password, updated_at
            FROM users 
            WHERE user_id = 'moonsoo'
        """)
        
        print(f"🔍 업데이트 확인:")
        print(f"   새 해시: {updated_user['hashed_password'][:50]}...")
        print(f"   업데이트 시간: {updated_user['updated_at']}")
        
        # 패스워드 검증 테스트
        is_valid = pwd_context.verify(new_password, updated_user['hashed_password'])
        print(f"🧪 패스워드 검증: {'✅ 성공' if is_valid else '❌ 실패'}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(update_password())