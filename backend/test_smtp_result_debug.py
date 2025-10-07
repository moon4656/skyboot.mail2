#!/usr/bin/env python3
"""
SMTP 발송 결과 반환값 디버깅 스크립트
send_email_smtp 메서드의 실제 반환값을 확인하여 성공 여부 판단 로직을 수정합니다.
"""

import asyncio
import sys
import os
import json
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.service.mail_service import MailService

async def test_smtp_result_format():
    """SMTP 발송 결과의 실제 반환값 형식을 확인"""
    
    print("🔍 SMTP 발송 결과 반환값 디버깅 시작")
    print("=" * 60)
    
    # MailService 인스턴스 생성 (DB 세션 없이)
    mail_service = MailService(db=None)
    
    # 테스트 데이터
    sender_email = "test@skyboot.local"
    recipient_emails = ["moon4656@gmail.com"]
    subject = "SMTP 결과 디버깅 테스트"
    body_text = "이것은 SMTP 발송 결과 반환값을 확인하는 테스트 메일입니다."
    
    print(f"📧 테스트 메일 정보:")
    print(f"   발송자: {sender_email}")
    print(f"   수신자: {recipient_emails}")
    print(f"   제목: {subject}")
    print()
    
    try:
        print("📤 send_email_smtp 메서드 호출...")
        result = await mail_service.send_email_smtp(
            sender_email=sender_email,
            recipient_emails=recipient_emails,
            subject=subject,
            body_text=body_text,
            body_html=None,
            org_id=None,
            attachments=None
        )
        
        print("✅ send_email_smtp 메서드 호출 완료!")
        print()
        
        # 결과 상세 분석
        print("🔍 반환값 상세 분석:")
        print(f"   타입: {type(result)}")
        print(f"   전체 내용: {result}")
        print()
        
        # JSON 형태로 예쁘게 출력
        print("📊 JSON 형태 결과:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print()
        
        # 성공 여부 판단 테스트
        print("🧪 성공 여부 판단 테스트:")
        
        # 현재 라우터에서 사용하는 방식
        success_check_1 = result.get('success', False)
        print(f"   result.get('success', False): {success_check_1} (타입: {type(success_check_1)})")
        
        # 다른 가능한 방식들
        success_check_2 = result.get('success') == True
        print(f"   result.get('success') == True: {success_check_2}")
        
        success_check_3 = 'success' in result and result['success']
        print(f"   'success' in result and result['success']: {success_check_3}")
        
        success_check_4 = bool(result.get('success'))
        print(f"   bool(result.get('success')): {success_check_4}")
        
        print()
        
        # 오류 정보 확인
        if 'error' in result:
            print(f"🚨 오류 정보:")
            print(f"   error: {result.get('error')}")
            print(f"   error_type: {result.get('error_type')}")
        else:
            print("✅ 오류 정보 없음")
        
        print()
        
        # 권장 성공 여부 판단 방식
        recommended_success = result.get('success', False) is True
        print(f"🎯 권장 성공 여부 판단: {recommended_success}")
        
        return result
        
    except Exception as e:
        print(f"❌ 예상치 못한 오류 발생: {str(e)}")
        import traceback
        print(f"❌ 상세 스택 트레이스:")
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    result = asyncio.run(test_smtp_result_format())
    
    print("=" * 60)
    if result:
        print("🎉 SMTP 결과 디버깅 완료!")
        
        # 라우터 수정 제안
        print()
        print("💡 라우터 수정 제안:")
        print("   현재: if not smtp_result.get('success', False):")
        print("   권장: if smtp_result.get('success') is not True:")
        print("   또는: if not smtp_result.get('success', False):")
    else:
        print("💥 SMTP 결과 디버깅 실패!")