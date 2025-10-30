#!/usr/bin/env python3
"""
조직 삭제 로직 테스트 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import uuid
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from app.config import settings
from app.model import Organization, User, MailUser
from app.service.organization_service import OrganizationService
from app.schemas.organization_schema import OrganizationCreate

async def test_organization_deletion():
    """조직 삭제 로직 테스트"""
    
    # 데이터베이스 연결
    engine = create_engine(settings.get_database_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("🧪 조직 삭제 로직 테스트 시작")
        print("=" * 50)
        
        # 1. 테스트용 조직 생성
        test_org_id = str(uuid.uuid4())
        test_org_code = f"testorg{uuid.uuid4().hex[:8]}"  # 언더스코어 제거
        
        print(f"📝 1. 테스트용 조직 생성 중...")
        print(f"   - org_id: {test_org_id}")
        print(f"   - org_code: {test_org_code}")
        
        org_service = OrganizationService(db)
        
        org_data = OrganizationCreate(
            name=f"테스트 조직 {test_org_code}",
            org_code=test_org_code,
            domain=f"{test_org_code}.com",  # 도메인 형식 수정
            subdomain=test_org_code,
            max_users=10,
            description="조직 삭제 테스트용 조직"
        )
        
        created_org = await org_service.create_organization(
            org_data=org_data,
            admin_email=f"admin@{test_org_code}.com",
            admin_password="testadmin123",
            admin_name="테스트 관리자"
        )
        print(f"✅ 테스트 조직 생성 완료: {created_org.name}")
        print(f"   - 생성된 조직 ID: {created_org.org_id}")
        
        # 실제 생성된 조직 ID 사용 (UUID가 다를 수 있음)
        actual_org_id = created_org.org_id
        
        # 2. 생성된 관리자 사용자 조회
        print(f"\n📝 2. 생성된 관리자 사용자 조회 중...")
        print(f"   - 조회할 조직 ID: {actual_org_id}")
        
        test_user = db.query(User).filter(User.org_id == actual_org_id).first()
        if test_user:
            print(f"✅ 관리자 사용자 조회 완료: {test_user.email}")
        else:
            print(f"❌ 관리자 사용자를 찾을 수 없습니다.")
            # 모든 사용자 조회해서 확인
            all_users = db.query(User).all()
            print(f"   - 전체 사용자 수: {len(all_users)}")
            for user in all_users:
                print(f"   - 사용자: {user.email}, org_id: {user.org_id}")
            return
        
        # 3. 생성된 mail_user 조회
        print(f"\n📝 3. 생성된 mail_user 조회 중...")
        
        test_mail_user = db.query(MailUser).filter(MailUser.org_id == actual_org_id).first()
        if test_mail_user:
            print(f"✅ mail_user 조회 완료: {test_mail_user.email}")
        else:
            print(f"❌ mail_user를 찾을 수 없습니다.")
            # 모든 mail_user 조회해서 확인
            all_mail_users = db.query(MailUser).all()
            print(f"   - 전체 mail_user 수: {len(all_mail_users)}")
            for mail_user in all_mail_users:
                print(f"   - mail_user: {mail_user.email}, org_id: {mail_user.org_id}")
            return
        
        # 4. 생성된 데이터 확인
        print(f"\n📊 4. 생성된 데이터 확인")
        
        org_count = db.query(Organization).filter(Organization.org_id == actual_org_id).count()
        user_count = db.query(User).filter(User.org_id == actual_org_id).count()
        mail_user_count = db.query(MailUser).filter(MailUser.org_id == actual_org_id).count()
        
        print(f"   - 조직 수: {org_count}")
        print(f"   - 사용자 수: {user_count}")
        print(f"   - mail_user 수: {mail_user_count}")
        
        # 5. 조직 강제 삭제 테스트
        print(f"\n🗑️ 5. 조직 강제 삭제 테스트")
        print(f"   - 삭제할 조직 ID: {actual_org_id}")
        
        success = await org_service.delete_organization(actual_org_id, force=True)
        
        if success:
            print(f"✅ 조직 삭제 성공")
        else:
            print(f"❌ 조직 삭제 실패")
            return
        
        # 6. 삭제 후 데이터 확인
        print(f"\n📊 6. 삭제 후 데이터 확인")
        
        org_count_after = db.query(Organization).filter(Organization.org_id == actual_org_id).count()
        user_count_after = db.query(User).filter(User.org_id == actual_org_id).count()
        mail_user_count_after = db.query(MailUser).filter(MailUser.org_id == actual_org_id).count()
        
        print(f"   - 조직 수: {org_count_after} (이전: {org_count})")
        print(f"   - 사용자 수: {user_count_after} (이전: {user_count})")
        print(f"   - mail_user 수: {mail_user_count_after} (이전: {mail_user_count})")
        
        # 7. 테스트 결과 평가
        print(f"\n📋 7. 테스트 결과 평가")
        
        if org_count_after == 0 and user_count_after == 0 and mail_user_count_after == 0:
            print(f"✅ 모든 테스트 통과: 조직과 관련 데이터가 모두 삭제됨")
        else:
            print(f"❌ 테스트 실패: 일부 데이터가 삭제되지 않음")
            if org_count_after > 0:
                print(f"   - 조직이 삭제되지 않음")
            if user_count_after > 0:
                print(f"   - 사용자가 삭제되지 않음")
            if mail_user_count_after > 0:
                print(f"   - mail_user가 삭제되지 않음")
        
        print("\n🎉 조직 삭제 로직 테스트 완료")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_organization_deletion())