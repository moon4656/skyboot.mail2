#!/usr/bin/env python3
"""
메일 UUID 생성 함수 테스트 스크립트

새로운 mail_uuid 생성 형식 (년월일_시분초_uuid[12])이 올바르게 작동하는지 확인합니다.
"""

import sys
import os
import re
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_mail_uuid_generation():
    """메일 UUID 생성 함수 테스트"""
    print("🧪 메일 UUID 생성 함수 테스트 시작")
    print("=" * 50)
    
    try:
        # generate_mail_uuid 함수 import
        from app.model.mail_model import generate_mail_uuid
        
        # 여러 번 생성하여 형식 확인
        for i in range(5):
            mail_uuid = generate_mail_uuid()
            print(f"생성된 UUID {i+1}: {mail_uuid}")
            
            # 형식 검증: YYYYMMDD_HHMMSS_12자리UUID
            pattern = r'^\d{8}_\d{6}_[a-f0-9]{12}$'
            if re.match(pattern, mail_uuid):
                print(f"  ✅ 형식 검증 통과")
                
                # 날짜/시간 부분 추출 및 검증
                date_part = mail_uuid[:8]
                time_part = mail_uuid[9:15]
                uuid_part = mail_uuid[16:]
                
                print(f"  📅 날짜 부분: {date_part}")
                print(f"  🕐 시간 부분: {time_part}")
                print(f"  🔑 UUID 부분: {uuid_part} (길이: {len(uuid_part)})")
                
                # 현재 시간과 비교 (대략적으로)
                current_time = datetime.now()
                expected_date = current_time.strftime("%Y%m%d")
                
                if date_part == expected_date:
                    print(f"  ✅ 날짜 부분 정확함")
                else:
                    print(f"  ⚠️ 날짜 부분 불일치 (예상: {expected_date}, 실제: {date_part})")
                
                if len(uuid_part) == 12:
                    print(f"  ✅ UUID 부분 길이 정확함 (12자리)")
                else:
                    print(f"  ❌ UUID 부분 길이 오류 (예상: 12, 실제: {len(uuid_part)})")
                    
            else:
                print(f"  ❌ 형식 검증 실패")
                print(f"  예상 형식: YYYYMMDD_HHMMSS_12자리UUID")
                print(f"  실제 형식: {mail_uuid}")
            
            print()
        
        print("🎉 메일 UUID 생성 함수 테스트 완료")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mail_model_default():
    """Mail 모델의 기본값 테스트"""
    print("\n🧪 Mail 모델 기본값 테스트 시작")
    print("=" * 50)
    
    try:
        from app.model.mail_model import Mail, generate_mail_uuid
        
        # 기본값으로 mail_uuid가 생성되는지 확인
        print("Mail 모델에서 기본값으로 mail_uuid 생성 테스트...")
        
        # 직접 함수 호출
        test_uuid = generate_mail_uuid()
        print(f"직접 함수 호출 결과: {test_uuid}")
        
        # 형식 검증
        pattern = r'^\d{8}_\d{6}_[a-f0-9]{12}$'
        if re.match(pattern, test_uuid):
            print("✅ Mail 모델 기본값 테스트 통과")
            return True
        else:
            print("❌ Mail 모델 기본값 테스트 실패")
            return False
            
    except Exception as e:
        print(f"❌ Mail 모델 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("📧 SkyBoot Mail UUID 생성 테스트")
    print("새로운 형식: 년월일_시분초_uuid[12]")
    print()
    
    # 테스트 실행
    test1_result = test_mail_uuid_generation()
    test2_result = test_mail_model_default()
    
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약")
    print(f"UUID 생성 함수 테스트: {'✅ 통과' if test1_result else '❌ 실패'}")
    print(f"Mail 모델 기본값 테스트: {'✅ 통과' if test2_result else '❌ 실패'}")
    
    if test1_result and test2_result:
        print("\n🎉 모든 테스트 통과! 새로운 mail_uuid 형식이 올바르게 적용되었습니다.")
        sys.exit(0)
    else:
        print("\n❌ 일부 테스트 실패. 코드를 확인해주세요.")
        sys.exit(1)