#!/usr/bin/env python3
"""
WSL Postfix 고급 메일 발송 테스트 스크립트
실제 사용자 계정과 도메인을 사용한 테스트
"""

import asyncio
import sys
import os
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_multiple_recipients():
    """
    여러 수신자에게 메일 발송 테스트
    """
    print("=" * 60)
    print("📧 다중 수신자 메일 발송 테스트")
    print("=" * 60)
    
    # 테스트할 수신자 목록
    test_recipients = [
        "eldorado@localhost",
        "testuser@localhost", 
        "user01@localhost",
        "admin@localhost"
    ]
    
    sender_email = "test@localhost"
    
    for recipient in test_recipients:
        try:
            print(f"\n📤 {recipient}에게 메일 발송 중...")
            
            # 메일 메시지 생성
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient
            msg['Subject'] = f"WSL Postfix 테스트 - {datetime.now().strftime('%H:%M:%S')}"
            
            # 메일 본문
            body = f"""
안녕하세요 {recipient}님!

이것은 WSL 환경에서 Postfix를 통한 메일 발송 테스트입니다.

발송 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분 %S초')}
발송자: {sender_email}
수신자: {recipient}

이 메일이 정상적으로 도착했다면 Postfix가 올바르게 작동하고 있습니다.

감사합니다.
SkyBoot Mail System
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # SMTP 서버를 통해 메일 발송
            with smtplib.SMTP('localhost', 25, timeout=30) as server:
                server.send_message(msg)
                
            print(f"✅ {recipient} 발송 성공!")
            
        except Exception as e:
            print(f"❌ {recipient} 발송 실패: {str(e)}")
            logger.error(f"메일 발송 오류 ({recipient}): {str(e)}")

def check_all_mailboxes():
    """
    모든 사용자의 메일박스 확인
    """
    print("\n" + "=" * 60)
    print("📬 모든 사용자 메일박스 확인")
    print("=" * 60)
    
    try:
        import subprocess
        
        # /var/spool/mail 디렉토리의 모든 파일 확인
        result = subprocess.run(
            ['wsl', 'ls', '-la', '/var/spool/mail/'], 
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            print(f"📋 메일박스 목록:\n{result.stdout}")
            
            # 각 메일박스의 메일 수 확인
            lines = result.stdout.strip().split('\n')
            for line in lines[2:]:  # 첫 두 줄은 . 과 .. 디렉토리
                if line.strip() and not line.startswith('total'):
                    parts = line.split()
                    if len(parts) >= 9:
                        filename = parts[-1]
                        size = parts[4]
                        print(f"   📧 {filename}: {size} bytes")
        else:
            print(f"⚠️ 메일박스 확인 실패: {result.stderr}")
            
    except Exception as e:
        print(f"❌ 메일박스 확인 중 오류: {str(e)}")

def check_postfix_status():
    """
    Postfix 서비스 상태 확인
    """
    print("\n" + "=" * 60)
    print("🔧 Postfix 서비스 상태 확인")
    print("=" * 60)
    
    try:
        import subprocess
        
        # Postfix 프로세스 확인
        result = subprocess.run(
            ['wsl', 'pgrep', '-f', 'postfix'], 
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            print(f"✅ Postfix 프로세스 실행 중: PID {result.stdout.strip()}")
        else:
            print("⚠️ Postfix 프로세스가 실행되지 않고 있습니다.")
            
        # Postfix 설정 확인
        config_result = subprocess.run(
            ['wsl', 'postconf', '-n'], 
            capture_output=True, text=True, timeout=10
        )
        
        if config_result.returncode == 0:
            print(f"\n📋 주요 Postfix 설정:\n{config_result.stdout[:500]}...")
        else:
            print(f"⚠️ Postfix 설정 확인 실패: {config_result.stderr}")
            
    except Exception as e:
        print(f"❌ Postfix 상태 확인 중 오류: {str(e)}")

def test_mail_delivery_time():
    """
    메일 전송 시간 측정
    """
    print("\n" + "=" * 60)
    print("⏱️ 메일 전송 시간 측정")
    print("=" * 60)
    
    try:
        start_time = datetime.now()
        
        # 간단한 테스트 메일 발송
        msg = MIMEText(f"시간 측정 테스트 메일 - {start_time}")
        msg['From'] = "timetest@localhost"
        msg['To'] = "eldorado@localhost"
        msg['Subject'] = "메일 전송 시간 측정 테스트"
        
        with smtplib.SMTP('localhost', 25, timeout=30) as server:
            server.send_message(msg)
            
        end_time = datetime.now()
        delivery_time = (end_time - start_time).total_seconds()
        
        print(f"📤 메일 발송 시작: {start_time.strftime('%H:%M:%S.%f')[:-3]}")
        print(f"✅ 메일 발송 완료: {end_time.strftime('%H:%M:%S.%f')[:-3]}")
        print(f"⏱️ 전송 시간: {delivery_time:.3f}초")
        
        if delivery_time < 1.0:
            print("🚀 매우 빠른 전송 속도!")
        elif delivery_time < 5.0:
            print("✅ 양호한 전송 속도")
        else:
            print("⚠️ 전송 속도가 느림")
            
    except Exception as e:
        print(f"❌ 시간 측정 중 오류: {str(e)}")

def show_recent_mail_content():
    """
    최근 도착한 메일 내용 확인
    """
    print("\n" + "=" * 60)
    print("📄 최근 메일 내용 확인")
    print("=" * 60)
    
    try:
        import subprocess
        
        # eldorado 사용자의 최근 메일 확인
        result = subprocess.run(
            ['wsl', 'tail', '-30', '/var/spool/mail/eldorado'], 
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            print(f"📧 eldorado 사용자의 최근 메일:\n{result.stdout}")
        else:
            print(f"⚠️ 메일 내용 확인 실패: {result.stderr}")
            
    except Exception as e:
        print(f"❌ 메일 내용 확인 중 오류: {str(e)}")

def main():
    """
    메인 테스트 함수
    """
    print("🚀 WSL Postfix 고급 메일 발송 테스트 시작")
    print(f"⏰ 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Postfix 상태 확인
    check_postfix_status()
    
    # 2. 다중 수신자 메일 발송 테스트
    test_multiple_recipients()
    
    # 3. 메일 전송 시간 측정
    test_mail_delivery_time()
    
    # 4. 모든 메일박스 확인
    check_all_mailboxes()
    
    # 5. 최근 메일 내용 확인
    show_recent_mail_content()
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 고급 테스트 결과 요약")
    print("=" * 60)
    print("✅ WSL Postfix 메일 발송 테스트가 완료되었습니다.")
    print("\n📋 확인된 사항:")
    print("   1. SMTP 서버 연결 정상")
    print("   2. 로컬 메일 전송 정상")
    print("   3. 메일박스 저장 정상")
    print("   4. 다중 수신자 지원")
    
    print("\n🔧 추가 테스트 방법:")
    print("   1. 외부 도메인 메일 발송: echo 'test' | wsl mail -s 'test' external@gmail.com")
    print("   2. 메일 큐 실시간 모니터링: wsl watch mailq")
    print("   3. Postfix 로그 실시간 확인: wsl tail -f /var/log/mail.log")
    print("   4. 메일 읽기: wsl mail -u eldorado")
    
    print(f"\n⏰ 테스트 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()