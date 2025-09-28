#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
사용자 조직 ID 수정 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.user import get_db
from app.model.user_model import User
from app.model.mail_model import MailUser
from app.model.organization_model import Organization
from sqlalchemy.orm import Session

def fix_user_org_id():
    """사용자 조직 ID 수정"""
    print("🔧 사용자 조직 ID 수정...")
    
    # 데이터베이스 연결
    db: Session = next(get_db())
    
    try:
        test_email = "test@example.com"
        
        # 테스트 사용자 조회
        user = db.query(User).filter(User.email == test_email).first()
        mail_user = db.query(MailUser).filter(MailUser.email == test_email).first()
        
        if not user:
            print(f"❌ 사용자 {test_email}를 찾을 수 없습니다.")
            return
            
        print(f"📧 현재 사용자 정보:")
        print(f"   - 이메일: {user.email}")
        print(f"   - 현재 조직 ID: {user.org_id}")
        
        # 기본 조직 찾기 (default-org-id 사용)
        default_org = db.query(Organization).filter(Organization.org_id == "default-org-id").first()
        
        if default_org:
            print(f"✅ 기본 조직 발견:")
            print(f"   - 조직 ID: {default_org.org_id}")
            print(f"   - 조직명: {default_org.name}")
            print(f"   - 활성 상태: {default_org.is_active}")
            
            # 사용자 조직 ID 업데이트
            user.org_id = default_org.org_id
            if mail_user:
                mail_user.org_id = default_org.org_id
                
            db.commit()
            
            print(f"✅ 사용자 조직 ID가 '{default_org.org_id}'로 업데이트되었습니다.")
            
        else:
            print(f"❌ 기본 조직을 찾을 수 없습니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_user_org_id()