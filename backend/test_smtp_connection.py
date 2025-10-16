#!/usr/bin/env python3
"""
SMTP 서버 연결 테스트 스크립트
SkyBoot Mail SaaS 프로젝트용
"""

import smtplib
import socket
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_smtp_connection():
    """SMTP 서버 연결을 테스트합니다."""
    
    print("🔍 SMTP 서버 연결 테스트 시작...")
    
    # 1. 소켓 연결 테스트
    print("\n1️⃣ 소켓 연결 테스트 (localhost:25)")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5초 타임아웃
        result = sock.connect_ex(('localhost', 25))
        sock.close()
        
        if result == 0:
            print("✅ 소켓 연결 성공")
        else:
            print(f"❌ 소켓 연결 실패 - 오류 코드: {result}")
            return False
    except Exception as e:
        print(f"❌ 소켓 연결 예외: {e}")
        return False
    
    # 2. SMTP 연결 테스트
    print("\n2️⃣ SMTP 연결 테스트")
    try:
        smtp_server = smtplib.SMTP()
        smtp_server.set_debuglevel(1)  # 디버그 모드 활성화
        print("📡 SMTP 서버에 연결 중...")
        smtp_server.connect('localhost', 25)
        print("✅ SMTP 연결 성공")
        
        # EHLO 명령 테스트
        print("\n3️⃣ EHLO 명령 테스트")
        smtp_server.ehlo()
        print("✅ EHLO 명령 성공")
        
        smtp_server.quit()
        print("✅ SMTP 연결 종료")
        return True
        
    except smtplib.SMTPConnectError as e:
        print(f"❌ SMTP 연결 오류: {e}")
    except smtplib.SMTPServerDisconnected as e:
        print(f"❌ SMTP 서버 연결 끊김: {e}")
    except socket.timeout as e:
        print(f"❌ SMTP 연결 타임아웃: {e}")
    except Exception as e:
        print(f"❌ SMTP 연결 예외: {e}")
    
    return False

def test_smtp_send():
    """간단한 테스트 메일 발송을 시도합니다."""
    
    print("\n4️⃣ 테스트 메일 발송 시도")
    try:
        smtp_server = smtplib.SMTP('localhost', 25)
        smtp_server.set_debuglevel(1)
        
        # 메일 생성
        msg = MIMEMultipart()
        msg['From'] = 'test@skyboot.co.kr'
        msg['To'] = 'moon4656@gmail.com'
        msg['Subject'] = 'SMTP 연결 테스트'
        
        body = "이것은 SMTP 서버 연결 테스트 메일입니다."
        msg.attach(MIMEText(body, 'plain'))
        
        # 메일 발송
        smtp_server.sendmail('test@skyboot.co.kr', 'moon4656@gmail.com', msg.as_string())
        smtp_server.quit()
        
        print("✅ 테스트 메일 발송 성공")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 메일 발송 실패: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 SkyBoot Mail SMTP 서버 연결 테스트")
    print("=" * 60)
    
    # 연결 테스트
    connection_success = test_smtp_connection()
    
    if connection_success:
        print("\n" + "=" * 60)
        # 메일 발송 테스트
        send_success = test_smtp_send()
        
        if send_success:
            print("\n🎉 모든 SMTP 테스트 성공!")
        else:
            print("\n⚠️ SMTP 연결은 성공했지만 메일 발송에 실패했습니다.")
    else:
        print("\n❌ SMTP 서버 연결에 실패했습니다.")
        print("\n🔧 해결 방법:")
        print("1. Postfix 서비스가 실행 중인지 확인")
        print("2. 방화벽 설정 확인")
        print("3. 포트 25가 다른 프로세스에 의해 사용되고 있는지 확인")
    
    print("=" * 60)