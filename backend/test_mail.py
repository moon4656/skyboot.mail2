#!/usr/bin/env python3
"""
메일 발송 테스트 스크립트
Postfix 연동 및 메일 발송 기능을 테스트합니다.
"""

import asyncio
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.routers.mail import send_email_via_postfix
from app.config import settings
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_mail_sending():
    """
    메일 발송 테스트 함수
    """
    print("=" * 50)
    print("SkyBoot Mail 발송 테스트")
    print("=" * 50)
    
    # 설정 정보 출력
    print(f"SMTP 호스트: {settings.SMTP_HOST}")
    print(f"SMTP 포트: {settings.SMTP_PORT}")
    print(f"발신자: {settings.SMTP_FROM_EMAIL}")
    print(f"발신자 이름: {settings.SMTP_FROM_NAME}")
    print("-" * 50)
    
    # 테스트 메일 정보
    test_emails = [
        {
            "to_email": "testuser@skyboot.local",
            "subject": "SkyBoot Mail 테스트 (to testuser)",
            "body": "안녕하세요, testuser님!\n\n이것은 SkyBoot Mail 시스템의 테스트 메일입니다.\n\n시스템이 정상적으로 작동하고 있습니다.\n\n감사합니다."
        }
    ]
    
    # 각 테스트 메일 발송
    for i, mail_data in enumerate(test_emails, 1):
        print(f"\n테스트 {i}: {mail_data['to_email']}로 메일 발송 중...")
        
        try:
            success, error_message = await send_email_via_postfix(
                to_email=mail_data["to_email"],
                subject=mail_data["subject"],
                body=mail_data["body"]
            )
            
            if success:
                print(f"✅ 성공: {mail_data['to_email']}")
            else:
                print(f"❌ 실패: {mail_data['to_email']}")
                print(f"   에러: {error_message}")
                
        except Exception as e:
            print(f"❌ 예외 발생: {str(e)}")
        
        # 테스트 간 간격
        if i < len(test_emails):
            print("   2초 대기 중...")
            await asyncio.sleep(2)
    
    print("\n" + "=" * 50)
    print("테스트 완료")
    print("=" * 50)

async def test_smtp_connection():
    """
    SMTP 서버 연결 테스트
    """
    print("\nSMTP 서버 연결 테스트...")
    
    try:
        import aiosmtplib
        import ssl
        
        # SSL 컨텍스트 생성 (인증서 검증 비활성화)
        tls_context = ssl.create_default_context()
        tls_context.check_hostname = False
        tls_context.verify_mode = ssl.CERT_NONE
        
        smtp_client = aiosmtplib.SMTP(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            timeout=10,
            tls_context=tls_context
        )
        
        await smtp_client.connect()
        print(f"✅ SMTP 서버 연결 성공: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
        
        # 인증 테스트 (설정된 경우)
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            await smtp_client.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            print("✅ SMTP 인증 성공")
        else:
            print("ℹ️  SMTP 인증 설정 없음 (인증 없이 발송)")
        
        await smtp_client.quit()
        
    except Exception as e:
        print(f"❌ SMTP 연결 실패: {str(e)}")
        return False
    
    return True

def check_environment():
    """
    환경 설정 확인
    """
    print("환경 설정 확인...")
    
    required_settings = [
        ('SMTP_HOST', settings.SMTP_HOST),
        ('SMTP_PORT', settings.SMTP_PORT),
        ('SMTP_FROM_EMAIL', settings.SMTP_FROM_EMAIL),
        ('SMTP_FROM_NAME', settings.SMTP_FROM_NAME)
    ]
    
    missing_settings = []
    
    for setting_name, setting_value in required_settings:
        if not setting_value:
            missing_settings.append(setting_name)
        else:
            print(f"✅ {setting_name}: {setting_value}")
    
    if missing_settings:
        print(f"❌ 누락된 설정: {', '.join(missing_settings)}")
        return False
    
    return True

async def main():
    """
    메인 테스트 함수
    """
    print("SkyBoot Mail 시스템 테스트 시작\n")
    
    # 1. 환경 설정 확인
    if not check_environment():
        print("\n환경 설정을 확인하고 다시 시도해주세요.")
        return
    
    # 2. SMTP 연결 테스트
    if not await test_smtp_connection():
        print("\nSMTP 서버 연결에 실패했습니다. 서버 상태를 확인해주세요.")
        return
    
    # 3. 메일 발송 테스트
    await test_mail_sending()
    
    print("\n모든 테스트가 완료되었습니다.")

if __name__ == "__main__":
    # 비동기 실행
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n\n테스트 중 오류 발생: {str(e)}")
        sys.exit(1)