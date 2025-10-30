#!/usr/bin/env python3
"""
SMTP 발송 수정 사항 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# .env 파일 로드
from dotenv import load_dotenv
load_dotenv()

import asyncio
from app.service.mail_service import MailService
from app.database.user import engine
from sqlalchemy.orm import sessionmaker

async def test_smtp_fix():
    """SMTP 발송 수정 사항 테스트"""
    
    print("🧪 SMTP 발송 수정 사항 테스트 시작")
    
    # 데이터베이스 세션 생성
    db = sessionmaker(bind=engine)()
    
    try:
        # MailService 인스턴스 생성
        mail_service = MailService(db)
        
        print(f"📧 SMTP 설정:")
        print(f"   서버: {mail_service.smtp_server}:{mail_service.smtp_port}")
        print(f"   사용자: {mail_service.smtp_username}")
        print(f"   TLS: {mail_service.use_tls}")
        
        # 테스트 메일 발송
        print(f"\n📤 테스트 메일 발송 시작...")
        
        result = await mail_service.send_email_smtp(
            sender_email="user01@skyboot.com",  # 수정된 사용자 이메일
            recipient_emails=["moon4656@hibiznet.com"],  # 테스트 수신자
            subject="🧪 SMTP 발송 수정 테스트",
            body_text="이 메일은 SMTP 발송 수정 사항을 테스트하기 위한 메일입니다.\n\n발신자 주소가 Gmail SMTP 설정에 맞게 자동으로 변경되는지 확인합니다.",
            org_id="3856a8c1-84a4-4019-9133-655cacab4bc9"
        )
        
        print(f"\n📊 발송 결과:")
        print(f"   성공: {result.get('success', False)}")
        print(f"   메시지: {result.get('message', 'N/A')}")
        if result.get('error'):
            print(f"   오류: {result.get('error')}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = asyncio.run(test_smtp_fix())
    if success:
        print("\n✅ SMTP 발송 수정 테스트 성공!")
    else:
        print("\n❌ SMTP 발송 수정 테스트 실패!")