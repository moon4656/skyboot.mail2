#!/usr/bin/env python3
"""데이터베이스의 사용자 정보를 확인하는 스크립트"""

import asyncio
import asyncpg
from app.config import settings

async def check_users():
    """데이터베이스의 사용자 정보를 확인합니다."""
    
    try:
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME
        )
        
        print("👥 사용자 목록 조회...")
        
        # 모든 사용자 조회
        users = await conn.fetch("""
            SELECT user_id, user_uuid, email, username, is_active, created_at, org_id
            FROM users 
            ORDER BY created_at DESC
            LIMIT 10;
        """)
        
        if users:
            print(f"\n📊 총 {len(users)}명의 사용자:")
            print("-" * 120)
            print(f"{'User ID':15} | {'User UUID':36} | {'Username':15} | {'Email':25} | {'Active':6} | {'Org ID':15}")
            print("-" * 120)
            
            for user in users:
                user_id = user['user_id'] or 'NULL'
                username = user['username'] or 'NULL'
                email = user['email'] or 'NULL'
                org_id = user['org_id'] or 'NULL'
                active = '✅' if user['is_active'] else '❌'
                
                print(f"{user_id:15} | {user['user_uuid']:36} | {username:15} | {email:25} | {active:6} | {org_id:15}")
        else:
            print("❌ 사용자가 없습니다.")
        
        # moonsoo 사용자 특별 조회
        print(f"\n🔍 'moonsoo' 사용자 검색...")
        moonsoo_users = await conn.fetch("""
            SELECT user_id, user_uuid, email, username, is_active, org_id, hashed_password
            FROM users 
            WHERE user_id = 'moonsoo' OR email LIKE '%moonsoo%' OR username LIKE '%moonsoo%'
        """)
        
        if moonsoo_users:
            for user in moonsoo_users:
                print(f"✅ 발견: user_id={user['user_id']}, username={user['username']}, email={user['email']}")
                print(f"   활성화: {user['is_active']}, 조직: {user['org_id']}")
                print(f"   패스워드 해시: {user['hashed_password'][:50]}...")
        else:
            print("❌ 'moonsoo' 사용자를 찾을 수 없습니다.")
            
        # 조직 정보도 확인
        print(f"\n🏢 조직 정보 조회...")
        orgs = await conn.fetch("""
            SELECT org_id, name, domain, is_active
            FROM organizations 
            ORDER BY created_at DESC
            LIMIT 5;
        """)
        
        if orgs:
            print(f"📊 총 {len(orgs)}개의 조직:")
            for org in orgs:
                active = '✅' if org['is_active'] else '❌'
                print(f"  org_id={org['org_id']}, 이름={org['name']}, 도메인={org['domain']}, 활성화={active}")
        else:
            print("❌ 조직이 없습니다.")
        
        await conn.close()
        
    except Exception as e:
        print(f'❌ 오류 발생: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_users())