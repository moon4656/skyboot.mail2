#!/usr/bin/env python3
"""
조직 수정 기능 테스트 스크립트

dict/list 타입 불일치 오류 수정 후 검증
"""
import asyncio
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import get_db
from app.service.organization_service import OrganizationService
from app.schemas.organization_schema import OrganizationUpdate


async def test_organization_update():
    """조직 수정 기능 테스트"""
    print("🧪 조직 수정 기능 테스트 시작")
    
    # 데이터베이스 세션 생성
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        # 조직 서비스 생성
        org_service = OrganizationService(db)
        
        # 기존 조직 목록 조회
        organizations = await org_service.list_organizations(limit=1)
        
        if not organizations:
            print("❌ 테스트할 조직이 없습니다.")
            return False
        
        test_org = organizations[0]
        print(f"📋 테스트 대상 조직: {test_org.name} (ID: {test_org.org_id})")
        
        # 조직 수정 데이터 준비
        update_data = OrganizationUpdate(
            description="테스트 수정된 설명",
            max_users=50,
            settings={
                "mail_retention_days": 180,
                "enable_spam_filter": True,
                "max_attachment_size_mb": 30
            }
        )
        
        print("🔄 조직 정보 수정 시도...")
        
        # 조직 수정 실행
        updated_org = await org_service.update_organization(
            org_id=test_org.org_id,
            org_data=update_data
        )
        
        if updated_org:
            print("✅ 조직 수정 성공!")
            print(f"   - 조직명: {updated_org.name}")
            print(f"   - 설명: {updated_org.description}")
            print(f"   - 최대 사용자: {updated_org.max_users}")
            print(f"   - 수정 시간: {updated_org.updated_at}")
            
            # 설정 확인
            settings = await org_service.get_organization_settings(test_org.org_id)
            if settings:
                print("📊 조직 설정 확인:")
                print(f"   - 설정 정보: {settings}")
            
            return True
        else:
            print("❌ 조직 수정 실패")
            return False
            
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()


async def main():
    """메인 함수"""
    print("=" * 60)
    print("🔧 조직 수정 기능 오류 수정 검증 테스트")
    print("=" * 60)
    
    success = await test_organization_update()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 모든 테스트 통과! 조직 수정 오류가 해결되었습니다.")
    else:
        print("❌ 테스트 실패! 추가 수정이 필요합니다.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())