#!/usr/bin/env python3
"""
Gmail SMTP 서버 연결 테스트 스크립트
SkyBoot Mail SaaS 프로젝트용 - Gmail SMTP 인증 테스트
"""

import smtplib
import socket
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def test_gmail_smtp_connection():
    """Gmail SMTP 서버 연결을 테스트합니다."""
    
    print("🔍 Gmail SMTP 서버 연결 테스트 시작...")
    
    # 환경 변수에서 SMTP 설정 읽기
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    print(f"📧 SMTP 서버: {smtp_host}:{smtp_port}")
    print(f"👤 사용자: {smtp_user}")
    print(f"🔑 비밀번호: {'설정됨' if smtp_password else '설정되지 않음'}")
    
    if not smtp_user or not smtp_password:
        print("❌ SMTP 사용자명 또는 비밀번호가 설정되지 않았습니다.")
        print("💡 .env 파일에서 SMTP_USER와 SMTP_PASSWORD를 확인하세요.")
        return False
    
    # 1. 소켓 연결 테스트
    print(f"\n1️⃣ 소켓 연결 테스트 ({smtp_host}:{smtp_port})")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10초 타임아웃
        result = sock.connect_ex((smtp_host, smtp_port))
        sock.close()
        
        if result == 0:
            print("✅ 소켓 연결 성공")
        else:
            print(f"❌ 소켓 연결 실패 - 오류 코드: {result}")
            return False
    except Exception as e:
        print(f"❌ 소켓 연결 예외: {e}")
        return False
    
    # 2. SMTP 연결 및 인증 테스트
    print("\n2️⃣ SMTP 연결 및 인증 테스트")
    try:
        smtp_server = smtplib.SMTP(smtp_host, smtp_port)
        smtp_server.set_debuglevel(1)  # 디버그 모드 활성화
        
        print("🔐 TLS 시작...")
        smtp_server.starttls()  # TLS 암호화 시작
        print("✅ TLS 연결 성공")
        
        print("🔑 SMTP 인증 중...")
        smtp_server.login(smtp_user, smtp_password)
        print("✅ SMTP 인증 성공")
        
        smtp_server.quit()
        print("✅ SMTP 연결 종료")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP 인증 실패: {e}")
        print("💡 Gmail 앱 비밀번호가 올바른지 확인하세요.")
    except smtplib.SMTPConnectError as e:
        print(f"❌ SMTP 연결 오류: {e}")
    except smtplib.SMTPServerDisconnected as e:
        print(f"❌ SMTP 서버 연결 끊김: {e}")
    except socket.timeout as e:
        print(f"❌ SMTP 연결 타임아웃: {e}")
    except Exception as e:
        print(f"❌ SMTP 연결 예외: {e}")
    
    return False

def test_gmail_smtp_send():
    """Gmail SMTP를 통해 테스트 메일 발송을 시도합니다."""
    
    print("\n3️⃣ Gmail SMTP 테스트 메일 발송")
    
    # 환경 변수에서 SMTP 설정 읽기
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('SMTP_FROM_EMAIL', smtp_user)
    
    try:
        smtp_server = smtplib.SMTP(smtp_host, smtp_port)
        smtp_server.set_debuglevel(1)
        smtp_server.starttls()
        smtp_server.login(smtp_user, smtp_password)
        
        # 메일 생성
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = smtp_user  # 자기 자신에게 발송
        msg['Subject'] = '🚀 SkyBoot Mail SMTP 연결 테스트 성공!'
        
        body = """
안녕하세요!

이 메일은 SkyBoot Mail SaaS 시스템의 Gmail SMTP 연결 테스트 메일입니다.

✅ SMTP 연결 성공
✅ 인증 성공  
✅ 메일 발송 성공

Gmail SMTP 설정이 정상적으로 작동하고 있습니다.

---
SkyBoot Mail System
        """
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 메일 발송
        print(f"📤 메일 발송 중... ({from_email} → {smtp_user})")
        smtp_server.sendmail(from_email, smtp_user, msg.as_string())
        smtp_server.quit()
        
        print("✅ 테스트 메일 발송 성공!")
        print(f"📬 {smtp_user} 메일함을 확인해보세요.")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 메일 발송 실패: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 SkyBoot Mail - Gmail SMTP 연결 테스트")
    print("=" * 60)
    
    # 연결 테스트
    connection_success = test_gmail_smtp_connection()
    
    if connection_success:
        print("\n" + "=" * 60)
        # 메일 발송 테스트
        send_success = test_gmail_smtp_send()
        
        if send_success:
            print("\n🎉 모든 Gmail SMTP 테스트 성공!")
            print("✅ SkyBoot Mail 시스템이 Gmail SMTP를 통해 메일을 발송할 수 있습니다.")
        else:
            print("\n⚠️ Gmail SMTP 연결은 성공했지만 메일 발송에 실패했습니다.")
    else:
        print("\n❌ Gmail SMTP 서버 연결에 실패했습니다.")
        print("\n🔧 해결 방법:")
        print("1. .env 파일의 SMTP_USER와 SMTP_PASSWORD 확인")
        print("2. Gmail 앱 비밀번호가 올바른지 확인")
        print("3. Gmail 2단계 인증이 활성화되어 있는지 확인")
        print("4. 인터넷 연결 상태 확인")
    
    print("=" * 60)