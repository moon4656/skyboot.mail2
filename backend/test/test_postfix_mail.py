#!/usr/bin/env python3
"""
WSL Postfix 메일 발송 테스트 스크립트
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

def test_smtp_connection():
    """
    SMTP 서버 연결 테스트
    """
    print("=" * 60)
    print("🔧 SMTP 서버 연결 테스트")
    print("=" * 60)
    
    smtp_configs = [
        {"host": "localhost", "port": 25, "name": "로컬 Postfix (포트 25)"},
        {"host": "localhost", "port": 587, "name": "로컬 Postfix (포트 587)"},
        {"host": "127.0.0.1", "port": 25, "name": "로컬호스트 (포트 25)"},
        {"host": "127.0.0.1", "port": 587, "name": "로컬호스트 (포트 587)"}
    ]
    
    for config in smtp_configs:
        try:
            print(f"\n📡 {config['name']} 연결 테스트...")
            with smtplib.SMTP(config['host'], config['port'], timeout=10) as server:
                server.noop()  # 연결 확인
                print(f"✅ {config['name']} 연결 성공!")
                
                # EHLO 응답 확인
                code, response = server.ehlo()
                print(f"   EHLO 응답: {code} - {response.decode('utf-8', errors='ignore')[:100]}...")
                
                return config  # 첫 번째 성공한 설정 반환
                
        except Exception as e:
            print(f"❌ {config['name']} 연결 실패: {str(e)}")
    
    print("\n⚠️ 모든 SMTP 서버 연결에 실패했습니다.")
    return None

def send_test_mail(smtp_config, sender_email="test@skyboot.local", recipient_email="testuser@skyboot.local"):
    """
    테스트 메일 발송
    """
    print("\n" + "=" * 60)
    print("📧 테스트 메일 발송")
    print("=" * 60)
    
    if not smtp_config:
        print("❌ SMTP 설정이 없어 메일 발송을 건너뜁니다.")
        return False
    
    try:
        # 메일 메시지 생성
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"WSL Postfix 테스트 메일 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 메일 본문
        body = f"""
안녕하세요!

이것은 WSL 환경에서 Postfix를 통한 메일 발송 테스트입니다.

발송 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분 %S초')}
SMTP 서버: {smtp_config['host']}:{smtp_config['port']}
발송자: {sender_email}
수신자: {recipient_email}

메일이 정상적으로 발송되었다면 Postfix가 올바르게 설정되어 있습니다.

감사합니다.
SkyBoot Mail System
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        print(f"📤 메일 발송 중...")
        print(f"   발송자: {sender_email}")
        print(f"   수신자: {recipient_email}")
        print(f"   SMTP: {smtp_config['host']}:{smtp_config['port']}")
        
        # SMTP 서버를 통해 메일 발송
        with smtplib.SMTP(smtp_config['host'], smtp_config['port'], timeout=30) as server:
            # 디버그 모드 활성화 (선택사항)
            # server.set_debuglevel(1)
            
            # 메일 발송
            server.send_message(msg)
            
        print(f"✅ 메일 발송 성공!")
        print(f"   메일이 {recipient_email}로 발송되었습니다.")
        return True
        
    except Exception as e:
        print(f"❌ 메일 발송 실패: {str(e)}")
        logger.error(f"메일 발송 오류: {str(e)}")
        return False

def check_mail_queue():
    """
    Postfix 메일 큐 상태 확인
    """
    print("\n" + "=" * 60)
    print("📬 Postfix 메일 큐 상태 확인")
    print("=" * 60)
    
    try:
        # mailq 명령어로 큐 상태 확인 (WSL에서 실행)
        import subprocess
        result = subprocess.run(['wsl', 'mailq'], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if output:
                print(f"📋 메일 큐 상태:\n{output}")
            else:
                print("✅ 메일 큐가 비어있습니다 (모든 메일이 발송됨)")
        else:
            print(f"⚠️ mailq 명령어 실행 실패: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⏰ mailq 명령어 실행 시간 초과")
    except FileNotFoundError:
        print("⚠️ WSL이 설치되지 않았거나 mailq 명령어를 찾을 수 없습니다.")
    except Exception as e:
        print(f"❌ 메일 큐 확인 중 오류: {str(e)}")

def check_postfix_logs():
    """
    Postfix 로그 확인
    """
    print("\n" + "=" * 60)
    print("📄 Postfix 로그 확인")
    print("=" * 60)
    
    try:
        import subprocess
        # 최근 Postfix 로그 확인
        result = subprocess.run(
            ['wsl', 'tail', '-n', '20', '/var/log/mail.log'], 
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if output:
                print(f"📋 최근 Postfix 로그 (마지막 20줄):\n{output}")
            else:
                print("⚠️ 로그가 비어있습니다.")
        else:
            print(f"⚠️ 로그 확인 실패: {result.stderr}")
            
    except Exception as e:
        print(f"❌ 로그 확인 중 오류: {str(e)}")

def main():
    """
    메인 테스트 함수
    """
    print("🚀 WSL Postfix 메일 발송 테스트 시작")
    print(f"⏰ 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. SMTP 연결 테스트
    smtp_config = test_smtp_connection()
    
    # 2. 테스트 메일 발송
    mail_sent = send_test_mail(smtp_config)
    
    # 3. 메일 큐 상태 확인
    check_mail_queue()
    
    # 4. Postfix 로그 확인
    check_postfix_logs()
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    print(f"SMTP 연결: {'✅ 성공' if smtp_config else '❌ 실패'}")
    print(f"메일 발송: {'✅ 성공' if mail_sent else '❌ 실패'}")
    
    if smtp_config and mail_sent:
        print("\n🎉 모든 테스트가 성공했습니다!")
        print("\n📋 다음 단계:")
        print("   1. WSL에서 'sudo tail -f /var/log/mail.log'로 실시간 로그 확인")
        print("   2. 수신자 메일박스 확인: ls -la /home/testuser/Maildir/new/")
        print("   3. 메일 내용 확인: cat /home/testuser/Maildir/new/*")
    else:
        print("\n⚠️ 일부 테스트가 실패했습니다.")
        print("\n🔧 문제 해결 방법:")
        print("   1. WSL에서 Postfix 서비스 상태 확인: sudo systemctl status postfix")
        print("   2. Postfix 서비스 시작: sudo systemctl start postfix")
        print("   3. Postfix 설정 확인: sudo postconf -n")
        print("   4. 방화벽 설정 확인: sudo ufw status")
    
    print(f"\n⏰ 테스트 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()