#!/usr/bin/env python3
"""
CASCADE 삭제 테스트 스크립트

외래 키 제약 조건이 CASCADE로 설정된 후 조직 삭제가 올바르게 작동하는지 테스트합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.mail import get_db
from app.service.organization_service import OrganizationService
from app.service.user_service import UserService
from app.service.mail_service import MailService
from sqlalchemy import text
import uuid

def test_cascade_deletion():
    """CASCADE 삭제 테스트를 실행합니다."""
    try:
        # 데이터베이스 연결
        db = next(get_db())
        
        print("🧪 CASCADE 삭제 테스트 시작")
        print("=" * 80)
        
        # 서비스 인스턴스 생성
        org_service = OrganizationService(db)
        user_service = UserService(db)
        mail_service = MailService(db)
        
        # 1. 테스트용 조직 생성
        test_org_name = f"TestOrg_{uuid.uuid4().hex[:8]}"
        print(f"📋 테스트 조직 생성: {test_org_name}")
        
        org_data = {
            "name": test_org_name,
            "domain": f"{test_org_name.lower()}.test.com",
            "max_users": 10,
            "features": ["email", "calendar"]
        }
        
        created_org = org_service.create_organization(
            org_data, 
            admin_email=f"admin@{org_data['domain']}", 
            admin_password="adminpassword123"
        )
        org_id = created_org["org_id"]
        print(f"✅ 조직 생성 완료: {org_id}")
        
        # 2. 테스트용 사용자 생성
        print(f"👤 테스트 사용자 생성")
        user_data = {
            "email": f"testuser@{org_data['domain']}",
            "password": "testpassword123",
            "full_name": "Test User",
            "role": "user"
        }
        
        created_user = user_service.create_user(user_data, org_id)
        user_id = created_user["user_id"]
        print(f"✅ 사용자 생성 완료: {user_id}")
        
        # 3. 삭제 전 데이터 상태 확인
        print(f"📊 삭제 전 데이터 상태 확인")
        
        # 조직 관련 데이터 개수 확인
        org_count = db.execute(text("SELECT COUNT(*) FROM organizations WHERE org_id = :org_id"), {"org_id": org_id}).scalar()
        user_count = db.execute(text("SELECT COUNT(*) FROM users WHERE org_id = :org_id"), {"org_id": org_id}).scalar()
        mail_user_count = db.execute(text("SELECT COUNT(*) FROM mail_users WHERE org_id = :org_id"), {"org_id": org_id}).scalar()
        mail_folder_count = db.execute(text("SELECT COUNT(*) FROM mail_folders WHERE org_id = :org_id"), {"org_id": org_id}).scalar()
        
        print(f"  - 조직: {org_count}개")
        print(f"  - 사용자: {user_count}개")
        print(f"  - 메일 사용자: {mail_user_count}개")
        print(f"  - 메일 폴더: {mail_folder_count}개")
        
        # 4. 조직 삭제 (CASCADE 테스트)
        print(f"🗑️ 조직 삭제 실행 (CASCADE 테스트)")
        
        result = org_service.delete_organization(org_id, force=True)
        print(f"✅ 조직 삭제 완료: {result}")
        
        # 5. 삭제 후 데이터 상태 확인
        print(f"📊 삭제 후 데이터 상태 확인")
        
        org_count_after = db.execute(text("SELECT COUNT(*) FROM organizations WHERE org_id = :org_id"), {"org_id": org_id}).scalar()
        user_count_after = db.execute(text("SELECT COUNT(*) FROM users WHERE org_id = :org_id"), {"org_id": org_id}).scalar()
        mail_user_count_after = db.execute(text("SELECT COUNT(*) FROM mail_users WHERE org_id = :org_id"), {"org_id": org_id}).scalar()
        mail_folder_count_after = db.execute(text("SELECT COUNT(*) FROM mail_folders WHERE org_id = :org_id"), {"org_id": org_id}).scalar()
        
        print(f"  - 조직: {org_count_after}개")
        print(f"  - 사용자: {user_count_after}개")
        print(f"  - 메일 사용자: {mail_user_count_after}개")
        print(f"  - 메일 폴더: {mail_folder_count_after}개")
        
        # 6. 테스트 결과 검증
        print(f"🔍 테스트 결과 검증")
        
        if org_count_after == 0 and user_count_after == 0 and mail_user_count_after == 0 and mail_folder_count_after == 0:
            print("✅ CASCADE 삭제 테스트 성공!")
            print("   모든 관련 데이터가 올바르게 삭제되었습니다.")
            return True
        else:
            print("❌ CASCADE 삭제 테스트 실패!")
            print("   일부 관련 데이터가 삭제되지 않았습니다.")
            return False
            
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_cascade_deletion()
    print("\n" + "=" * 80)
    if success:
        print("🎉 CASCADE 삭제 테스트 완료 - 성공!")
    else:
        print("💥 CASCADE 삭제 테스트 완료 - 실패!")
    print("=" * 80)