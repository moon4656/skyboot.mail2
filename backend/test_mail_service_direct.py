#!/usr/bin/env python3
"""
MailService의 send_email_smtp 메서드를 직접 테스트하는 스크립트
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.service.mail_service import MailService

async def test_mail_service_direct():
    """MailService의 send_email_smtp 메서드를 직접 테스트"""
    
    print("🧪 MailService send_email_smtp 직접 테스트 시작")
    print("=" * 60)
    
    # MailService 인스턴스 생성 (DB 세션 없이)
    mail_service = MailService(db=None)
    
    # 테스트 데이터
    sender_email = "test@skyboot.local"
    recipient_emails = ["moon4656@gmail.com"]
    subject = "MailService 직접 테스트"
    body_text = "이것은 MailService의 send_email_smtp 메서드를 직접 테스트하는 메일입니다."
    
    print(f"📧 테스트 메일 정보:")
    print(f"   발송자: {sender_email}")
    print(f"   수신자: {recipient_emails}")
    print(f"   제목: {subject}")
    print(f"   본문: {body_text}")
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
        print(f"📊 결과: {result}")
        
        if result.get('success', False):
            print("🎉 메일 발송 성공!")
        else:
            print("❌ 메일 발송 실패!")
            print(f"   오류: {result.get('error', '알 수 없는 오류')}")
            print(f"   오류 타입: {result.get('error_type', '알 수 없음')}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ 예상치 못한 오류 발생: {str(e)}")
        import traceback
        print(f"❌ 상세 스택 트레이스:")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mail_service_direct())
    
    print("=" * 60)
    if success:
        print("🎉 MailService 테스트 성공!")
    else:
        print("💥 MailService 테스트 실패!")