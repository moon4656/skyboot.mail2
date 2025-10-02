#!/usr/bin/env python3
"""
Settings 필드 오류 수정 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import get_db
from app.service.organization_service import OrganizationService

async def test_organization_settings_fix():
    """조직 settings 필드 오류 수정 테스트"""
    
    # 데이터베이스 세션 생성
    db: Session = next(get_db())
    
    try:
        # OrganizationService 인스턴스 생성
        org_service = OrganizationService(db)
        
        # 특정 조직 ID로 테스트 (사용자가 제공한 org_id)
        test_org_id = "3856a8c1-84a4-4019-9133-655cacab4bc9"
        
        print(f"🔍 조직 조회 테스트 시작 - org_id: {test_org_id}")
        
        # 1. get_organization_by_id 테스트
        print("\n1. get_organization_by_id 테스트...")
        try:
            org_response = await org_service.get_organization_by_id(test_org_id)
            if org_response:
                print(f"✅ 조직 조회 성공: {org_response.name}")
                print(f"   - org_id: {org_response.org_id}")
                print(f"   - max_users: {org_response.max_users}")
                print(f"   - settings: {org_response.settings}")
            else:
                print("❌ 조직을 찾을 수 없습니다.")
        except Exception as e:
            print(f"❌ get_organization_by_id 오류: {str(e)}")
        
        # 2. get_organization 테스트
        print("\n2. get_organization 테스트...")
        try:
            org_response = await org_service.get_organization(test_org_id)
            if org_response:
                print(f"✅ 조직 조회 성공: {org_response.name}")
                print(f"   - org_id: {org_response.org_id}")
                print(f"   - max_users: {org_response.max_users}")
                print(f"   - settings: {org_response.settings}")
            else:
                print("❌ 조직을 찾을 수 없습니다.")
        except Exception as e:
            print(f"❌ get_organization 오류: {str(e)}")
        
        # 3. list_organizations 테스트
        print("\n3. list_organizations 테스트...")
        try:
            org_list = await org_service.list_organizations(limit=5)
            print(f"✅ 조직 목록 조회 성공: {len(org_list)}개 조직")
            for org in org_list:
                print(f"   - {org.name} (ID: {org.org_id})")
                print(f"     max_users: {org.max_users}, settings: {org.settings}")
        except Exception as e:
            print(f"❌ list_organizations 오류: {str(e)}")
        
        # 4. get_organization_stats 테스트
        print("\n4. get_organization_stats 테스트...")
        try:
            stats = await org_service.get_organization_stats(test_org_id)
            if stats:
                print(f"✅ 조직 통계 조회 성공")
                print(f"   - 총 사용자 수: {stats.total_users}")
                print(f"   - 메일 사용자 수: {stats.mail_users}")
            else:
                print("❌ 조직 통계를 찾을 수 없습니다.")
        except Exception as e:
            print(f"❌ get_organization_stats 오류: {str(e)}")
        
        print("\n🎉 모든 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_organization_settings_fix())