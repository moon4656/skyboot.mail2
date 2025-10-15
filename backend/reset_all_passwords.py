#!/usr/bin/env python3
"""
모든 사용자의 패스워드를 'test'로 일괄 변경하는 스크립트

⚠️ 보안 경고: 이 스크립트는 모든 사용자의 패스워드를 동일한 값으로 변경합니다.
개발/테스트 환경에서만 사용하고, 프로덕션 환경에서는 절대 사용하지 마세요.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.model.user_model import User
from app.model.organization_model import Organization
from app.service.auth_service import AuthService
from app.config import settings

def reset_all_passwords():
    """
    모든 사용자의 패스워드를 'test'로 변경합니다.
    """
    print("=" * 80)
    print("⚠️  모든 사용자 패스워드 일괄 변경 작업")
    print("=" * 80)
    print("🔒 새 패스워드: 'test'")
    print("⚠️  보안 경고: 이 작업은 모든 사용자의 패스워드를 동일하게 만듭니다.")
    print("   개발/테스트 환경에서만 사용하세요!")
    print()
    
    # 사용자 확인
    confirm = input("정말로 모든 사용자의 패스워드를 'test'로 변경하시겠습니까? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ 작업이 취소되었습니다.")
        return
    
    try:
        # 데이터베이스 연결
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        # 모든 사용자 조회
        users = session.query(User).all()
        
        if not users:
            print("❌ 등록된 사용자가 없습니다.")
            session.close()
            return
        
        print(f"📊 총 {len(users)}명의 사용자 패스워드를 변경합니다.\n")
        
        # 새 패스워드 해시 생성
        new_password = "test"
        new_password_hash = AuthService.get_password_hash(new_password)
        
        print(f"🔐 새 패스워드 해시: {new_password_hash[:50]}...\n")
        
        # 각 사용자의 패스워드 변경
        updated_count = 0
        for i, user in enumerate(users, 1):
            try:
                # 조직 정보 조회
                organization = session.query(Organization).filter(Organization.org_id == user.org_id).first()
                org_name = organization.name if organization else "알 수 없음"
                
                print(f"{i}. 패스워드 변경 중...")
                print(f"   - 이메일: {user.email}")
                print(f"   - 역할: {user.role}")
                print(f"   - 조직: {org_name}")
                print(f"   - 이전 해시: {user.hashed_password[:50]}...")
                
                # 패스워드 해시 업데이트
                user.hashed_password = new_password_hash
                session.add(user)
                
                print(f"   - 새 해시: {new_password_hash[:50]}...")
                print(f"   ✅ 변경 완료\n")
                
                updated_count += 1
                
            except Exception as e:
                print(f"   ❌ 오류 발생: {str(e)}\n")
                continue
        
        # 변경사항 커밋
        session.commit()
        session.close()
        
        print("=" * 80)
        print(f"✅ 패스워드 일괄 변경 완료!")
        print(f"📊 성공: {updated_count}명 / 전체: {len(users)}명")
        print("=" * 80)
        print()
        print("🔑 변경된 로그인 정보:")
        print("   - admin@skyboot.mail / test")
        print("   - user01@skyboot.mail / test")
        print("   - testuser@skyboot.mail / test")
        print()
        print("⚠️  보안 알림: 모든 사용자가 동일한 패스워드를 사용하고 있습니다.")
        print("   프로덕션 환경에서는 각 사용자가 고유한 패스워드를 설정하도록 하세요.")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reset_all_passwords()