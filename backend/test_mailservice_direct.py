#!/usr/bin/env python3
"""
MailService 직접 테스트 스크립트
SMTP 연결 문제를 디버깅하기 위한 스크립트
"""
import asyncio
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.service.mail_service import MailService

async def test_mailservice_direct():
    """MailService를 직접 테스트합니다."""
    print("🧪 MailService 직접 테스트 시작")
    print("=" * 60)
    
    try:
        # MailService 인스턴스 생성 (db 세션 없이)
        print("📦 MailService 인스턴스 생성 중...")
        mail_service = MailService()
        print("✅ MailService 인스턴스 생성 완료")
        
        # SMTP 설정 확인
        print(f"🔧 SMTP 설정:")
        print(f"   - 서버: {mail_service.smtp_server}:{mail_service.smtp_port}")
        print(f"   - TLS: {mail_service.use_tls}")
        print(f"   - 사용자명: {mail_service.smtp_username}")
        print(f"   - 비밀번호 설정됨: {'예' if mail_service.smtp_password else '아니오'}")
        
        # 메일 발송 테스트
        print("\n📤 메일 발송 테스트 시작...")
        result = await mail_service.send_email_smtp(
            sender_email="test@skyboot.local",
            recipient_emails=["moon4656@gmail.com"],
            subject="MailService 직접 테스트",
            body_text="이것은 MailService 직접 테스트 메일입니다.",
            body_html="<p>이것은 <strong>MailService 직접 테스트</strong> 메일입니다.</p>"
        )
        
        print("\n📊 테스트 결과:")
        print(f"   - 성공 여부: {result.get('success', False)}")
        if result.get('success'):
            print(f"   - 메시지: {result.get('message')}")
            print(f"   - 수신자 수: {result.get('recipients_count')}")
            print(f"   - SMTP 서버: {result.get('smtp_server')}")
        else:
            print(f"   - 오류: {result.get('error')}")
            print(f"   - 오류 타입: {result.get('error_type')}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ 테스트 중 예외 발생: {str(e)}")
        print(f"예외 타입: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mailservice_direct())
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 MailService 직접 테스트 성공!")
        print("📧 moon4656@gmail.com 메일함을 확인해보세요.")
    else:
        print("❌ MailService 직접 테스트 실패!")
        print("🔍 로그를 확인하여 문제를 파악하세요.")