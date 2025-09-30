#!/usr/bin/env python3
"""
UUID 수정 사항 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.model.user_model import User, generate_user_uuid
from app.model.mail_model import MailUser, generate_mail_user_uuid, generate_mail_uuid
from app.model.organization_model import Organization
from app.database.user import get_db
from sqlalchemy.orm import Session
import uuid

def test_uuid_generation():
    """UUID 생성 함수들을 테스트합니다."""
    print("🧪 UUID 생성 함수 테스트 시작...")
    
    try:
        # 1. generate_user_uuid 테스트
        print("\n1. generate_user_uuid 테스트:")
        user_uuid = generate_user_uuid()
        print(f"   생성된 UUID: {user_uuid}")
        print(f"   타입: {type(user_uuid)}")
        print(f"   길이: {len(user_uuid)}")
        
        # UUID 형식 검증
        try:
            uuid.UUID(user_uuid)
            print("   ✅ 유효한 UUID 형식")
        except ValueError:
            print("   ❌ 잘못된 UUID 형식")
            return False
        
        # 2. generate_mail_user_uuid 테스트
        print("\n2. generate_mail_user_uuid 테스트:")
        mail_user_uuid = generate_mail_user_uuid()
        print(f"   생성된 UUID: {mail_user_uuid}")
        print(f"   타입: {type(mail_user_uuid)}")
        print(f"   길이: {len(mail_user_uuid)}")
        
        # UUID 형식 검증
        try:
            uuid.UUID(mail_user_uuid)
            print("   ✅ 유효한 UUID 형식")
        except ValueError:
            print("   ❌ 잘못된 UUID 형식")
            return False
        
        # 3. generate_mail_uuid 테스트
        print("\n3. generate_mail_uuid 테스트:")
        mail_uuid = generate_mail_uuid()
        print(f"   생성된 메일 UUID: {mail_uuid}")
        print(f"   타입: {type(mail_uuid)}")
        print(f"   길이: {len(mail_uuid)}")
        
        # 메일 UUID 형식 검증 (YYYYMMDD_HHMMSS_uuid 형태)
        parts = mail_uuid.split('_')
        if len(parts) == 3:
            print("   ✅ 올바른 메일 UUID 형식 (날짜_시간_uuid)")
        else:
            print("   ❌ 잘못된 메일 UUID 형식")
            return False
        
        # 4. 고유성 테스트
        print("\n4. UUID 고유성 테스트:")
        uuids = set()
        for i in range(100):
            new_uuid = generate_user_uuid()
            if new_uuid in uuids:
                print(f"   ❌ 중복 UUID 발견: {new_uuid}")
                return False
            uuids.add(new_uuid)
        print("   ✅ 100개 UUID 모두 고유함")
        
        print("\n✅ 모든 UUID 생성 함수 테스트 통과!")
        return True
        
    except Exception as e:
        print(f"\n❌ UUID 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_model_creation():
    """모델 생성 테스트 (실제 DB 연결 없이)"""
    print("\n🧪 모델 생성 테스트 시작...")
    
    try:
        # User 모델의 default 함수 테스트
        print("\n1. User 모델 default 함수 테스트:")
        user_default = User.__table__.columns['user_uuid'].default
        if user_default and user_default.arg:
            default_value = user_default.arg(None)  # ctx 매개변수 전달
            print(f"   기본값 생성: {default_value}")
            print(f"   타입: {type(default_value)}")
            
            # UUID 형식 검증
            try:
                uuid.UUID(default_value)
                print("   ✅ 유효한 UUID 형식")
            except ValueError:
                print("   ❌ 잘못된 UUID 형식")
                return False
        else:
            print("   ❌ default 함수가 설정되지 않음")
            return False
        
        # MailUser 모델의 default 함수 테스트
        print("\n2. MailUser 모델 default 함수 테스트:")
        mail_user_default = MailUser.__table__.columns['user_uuid'].default
        if mail_user_default and mail_user_default.arg:
            default_value = mail_user_default.arg(None)  # ctx 매개변수 전달
            print(f"   기본값 생성: {default_value}")
            print(f"   타입: {type(default_value)}")
            
            # UUID 형식 검증
            try:
                uuid.UUID(default_value)
                print("   ✅ 유효한 UUID 형식")
            except ValueError:
                print("   ❌ 잘못된 UUID 형식")
                return False
        else:
            print("   ❌ default 함수가 설정되지 않음")
            return False
        
        print("\n✅ 모든 모델 생성 테스트 통과!")
        return True
        
    except Exception as e:
        print(f"\n❌ 모델 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("UUID 수정 사항 테스트")
    print("=" * 60)
    
    # UUID 생성 함수 테스트
    uuid_test_result = test_uuid_generation()
    
    # 모델 생성 테스트
    model_test_result = test_model_creation()
    
    print("\n" + "=" * 60)
    print("테스트 결과 요약:")
    print("=" * 60)
    print(f"UUID 생성 함수 테스트: {'✅ 통과' if uuid_test_result else '❌ 실패'}")
    print(f"모델 생성 테스트: {'✅ 통과' if model_test_result else '❌ 실패'}")
    
    if uuid_test_result and model_test_result:
        print("\n🎉 모든 테스트 통과! UUID 수정이 성공적으로 완료되었습니다.")
        sys.exit(0)
    else:
        print("\n💥 일부 테스트 실패! 추가 수정이 필요합니다.")
        sys.exit(1)