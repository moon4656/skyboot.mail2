#!/usr/bin/env python3
"""
직접 조직 삭제 테스트 스크립트
불필요한 UPDATE 쿼리가 발생하지 않는지 확인
"""

import asyncio
from sqlalchemy.orm import Session
from app.database.mail import get_db
from app.service.organization_service import OrganizationService

async def test_direct_organization_deletion():
    """직접 조직 삭제 테스트"""
    print("🔍 직접 조직 삭제 테스트 시작")
    
    # 데이터베이스 세션 생성
    db = next(get_db())
    org_service = OrganizationService(db)
    
    try:
        # 방금 생성된 조직 ID
        org_id = "299b2341-5e7c-46cd-8e49-5bdfc6829caf"
        
        print(f"\n🗑️ 조직 삭제 시도: {org_id}")
        print("📋 서버 로그를 확인하여 다음을 확인하세요:")
        print("   - UPDATE mail_users SET org_id=... 쿼리가 없어야 함")
        print("   - DELETE FROM organizations WHERE org_id=... 쿼리만 있어야 함")
        print()
        
        # 조직 삭제 (force=True)
        await org_service.delete_organization(org_id, force=True)
        
        print("✅ 조직 삭제 완료")
        
    except Exception as e:
        print(f"❌ 조직 삭제 중 오류: {e}")
    finally:
        db.close()
    
    print("\n🔍 직접 삭제 테스트 완료")

if __name__ == "__main__":
    asyncio.run(test_direct_organization_deletion())