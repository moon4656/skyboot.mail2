#!/usr/bin/env python3
"""
조직 생성 과정 디버깅 스크립트

조직 생성 시 발생하는 문제를 단계별로 진단합니다.
"""

import asyncio
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database.user import get_db
from app.service.organization_service import OrganizationService
from app.schemas.organization_schema import OrganizationCreate
from app.model.organization_model import Organization
from app.model.user_model import User
from app.model.mail_model import MailUser

async def debug_organization_creation():
    """조직 생성 과정 디버깅"""
    
    print("🔍 조직 생성 과정 디버깅 시작")
    
    # 데이터베이스 연결
    db: Session = next(get_db())
    org_service = OrganizationService(db)
    
    try:
        # 1. 테스트 조직 데이터 준비
        print("\n📝 1. 테스트 조직 데이터 준비")
        
        test_org_data = OrganizationCreate(
            name="디버그 테스트 조직",
            org_code="debugtest",
            subdomain="debugtest",
            domain="debugtest.com",
            description="디버깅용 테스트 조직",
            max_users=10,
            max_storage_gb=5
        )
        
        admin_email = "admin@debugtest.com"
        admin_password = "testpass123"
        admin_name = "디버그 관리자"
        
        print(f"   - 조직명: {test_org_data.name}")
        print(f"   - 조직 코드: {test_org_data.org_code}")
        print(f"   - 관리자 이메일: {admin_email}")
        
        # 2. 기존 조직 확인 및 정리
        print("\n🧹 2. 기존 테스트 데이터 정리")
        
        existing_org = db.query(Organization).filter(
            Organization.org_code == test_org_data.org_code
        ).first()
        
        if existing_org:
            org_name = existing_org.name  # 삭제 전에 이름 저장
            org_id = existing_org.org_id  # 삭제 전에 ID 저장
            print(f"   - 기존 조직 발견: {org_name} (ID: {org_id})")
            
            # CASCADE 설정을 활용하여 조직만 삭제 (관련 데이터 자동 삭제)
            from sqlalchemy import text
            result = db.execute(
                text("DELETE FROM organizations WHERE org_id = :org_id"),
                {"org_id": org_id}
            )
            db.commit()
            
            if result.rowcount > 0:
                print(f"   - 조직 및 관련 데이터 삭제 완료 (CASCADE): {org_name}")
            else:
                print(f"   - 삭제할 조직을 찾을 수 없음: {org_id}")
        else:
            print("   - 기존 테스트 데이터 없음")
        
        # 3. 조직 생성 시도
        print("\n🏢 3. 조직 생성 시도")
        
        try:
            created_org = await org_service.create_organization(
                org_data=test_org_data,
                admin_email=admin_email,
                admin_password=admin_password,
                admin_name=admin_name
            )
            
            print(f"✅ 조직 생성 성공: {created_org.name}")
            print(f"   - 조직 ID: {created_org.org_id}")
            
            # 4. 생성된 데이터 확인
            print("\n📊 4. 생성된 데이터 확인")
            
            # 조직 확인
            org_count = db.query(Organization).filter(
                Organization.org_id == created_org.org_id
            ).count()
            print(f"   - 조직 수: {org_count}")
            
            # 사용자 확인
            users = db.query(User).filter(User.org_id == created_org.org_id).all()
            print(f"   - 사용자 수: {len(users)}")
            for user in users:
                print(f"     * {user.email} (ID: {user.user_id}, UUID: {user.user_uuid})")
            
            # 메일 사용자 확인
            mail_users = db.query(MailUser).filter(MailUser.org_id == created_org.org_id).all()
            print(f"   - 메일 사용자 수: {len(mail_users)}")
            for mail_user in mail_users:
                print(f"     * {mail_user.email} (ID: {mail_user.user_id}, UUID: {mail_user.user_uuid})")
            
            # 5. 조직 삭제 테스트
            print("\n🗑️ 5. 조직 삭제 테스트")
            
            success = await org_service.delete_organization(created_org.org_id, force=True)
            
            if success:
                print("✅ 조직 삭제 성공")
                
                # 삭제 후 데이터 확인
                print("\n📊 6. 삭제 후 데이터 확인")
                
                org_count_after = db.query(Organization).filter(
                    Organization.org_id == created_org.org_id
                ).count()
                user_count_after = db.query(User).filter(
                    User.org_id == created_org.org_id
                ).count()
                mail_user_count_after = db.query(MailUser).filter(
                    MailUser.org_id == created_org.org_id
                ).count()
                
                print(f"   - 조직 수: {org_count_after}")
                print(f"   - 사용자 수: {user_count_after}")
                print(f"   - 메일 사용자 수: {mail_user_count_after}")
                
                if org_count_after == 0 and user_count_after == 0 and mail_user_count_after == 0:
                    print("✅ 모든 관련 데이터가 성공적으로 삭제되었습니다!")
                else:
                    print("⚠️ 일부 데이터가 삭제되지 않았습니다.")
            else:
                print("❌ 조직 삭제 실패")
                
        except Exception as e:
            print(f"❌ 조직 생성 오류: {str(e)}")
            import traceback
            print(f"상세 오류: {traceback.format_exc()}")
            
    except Exception as e:
        print(f"❌ 전체 프로세스 오류: {str(e)}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        
    finally:
        db.close()
        print("\n🔍 디버깅 완료")

if __name__ == "__main__":
    asyncio.run(debug_organization_creation())