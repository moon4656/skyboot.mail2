#!/usr/bin/env python3
"""
조직 삭제 최종 테스트 - UPDATE 쿼리 방지 확인
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.mail import get_db
from app.service.organization_service import OrganizationService
from app.schemas.organization_schema import OrganizationCreate
import asyncio

async def test_organization_deletion():
    """조직 삭제 테스트 - UPDATE 쿼리가 실행되지 않는지 확인"""
    
    db = next(get_db())
    org_service = OrganizationService(db)
    
    try:
        print("🏢 조직 생성 중...")
        
        # 조직 생성
        org_data = OrganizationCreate(
            name="테스트 조직 최종",
            org_code="TESTFINAL",
            subdomain="testfinal",
            domain="testfinal.example.com",
            description="최종 테스트용 조직",
            max_storage_gb=10
        )
        
        result = await org_service.create_organization(
            org_data=org_data,
            admin_email="admin@testfinal.example.com",
            admin_password="TestPassword123!",
            admin_name="최종 테스트 관리자"
        )
        org_id = result.org_id
        
        print(f"✅ 조직 생성 완료: {result.name} (ID: {org_id})")
        
        # 2초 대기
        print("⏳ 2초 대기 중...")
        await asyncio.sleep(2)
        
        # 조직 강제 삭제 (하드 삭제)
        print(f"🗑️ 조직 강제 삭제 중: {org_id}")
        
        deletion_result = await org_service.delete_organization(org_id, force=True)
        
        if deletion_result:
            print("✅ 조직 삭제 완료!")
            print("📋 서버 로그를 확인하여 다음을 검증하세요:")
            print("   ❌ UPDATE mail_users SET org_id=... 쿼리가 실행되지 않았는지")
            print("   ✅ DELETE FROM organizations WHERE org_id=... 쿼리만 실행되었는지")
        else:
            print("❌ 조직 삭제 실패")
            
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_organization_deletion())