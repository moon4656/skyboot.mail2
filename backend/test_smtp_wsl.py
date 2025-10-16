#!/usr/bin/env python3
"""
WSL Postfix SMTP 서버 연결 테스트
"""
import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import time

def test_smtp_connection():
    """WSL Postfix SMTP 서버 연결 테스트"""
    
    # WSL IP 및 포트 설정
    smtp_host = "172.18.0.233"
    smtp_port = 25
    
    print(f"🔍 SMTP 서버 연결 테스트 시작")
    print(f"📍 서버: {smtp_host}:{smtp_port}")
    print("-" * 50)
    
    try:
        # 1. 소켓 연결 테스트
        print(f"1️⃣ 소켓 연결 테스트...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10초 타임아웃
        result = sock.connect_ex((smtp_host, smtp_port))
        
        if result == 0:
            print(f"✅ 소켓 연결 성공: {smtp_host}:{smtp_port}")
            sock.close()
        else:
            print(f"❌ 소켓 연결 실패: {result}")
            return False
            
        # 2. SMTP 연결 테스트
        print(f"2️⃣ SMTP 프로토콜 연결 테스트...")
        
        # SMTP 서버 연결
        server = smtplib.SMTP(timeout=10)
        server.set_debuglevel(1)  # 디버그 모드 활성화
        
        print(f"📡 SMTP 서버 연결 중: {smtp_host}:{smtp_port}")
        server.connect(smtp_host, smtp_port)
        
        print(f"👋 SMTP 서버 인사...")
        server.ehlo()
        
        print(f"✅ SMTP 연결 성공!")
        
        # 3. 테스트 메일 발송
        print(f"3️⃣ 테스트 메일 발송...")
        
        # 메일 구성
        msg = MIMEMultipart()
        msg['From'] = "test@skyboot.mail"
        msg['To'] = "admin@skyboot.mail"
        msg['Subject'] = "SkyBoot Mail SMTP 테스트"
        
        body = """
        안녕하세요!
        
        이것은 SkyBoot Mail SaaS 시스템의 SMTP 연결 테스트 메일입니다.
        
        WSL Postfix 서버가 정상적으로 작동하고 있습니다.
        
        감사합니다.
        SkyBoot Mail 시스템
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 메일 발송
        text = msg.as_string()
        server.sendmail("test@skyboot.mail", ["admin@skyboot.mail"], text)
        
        print(f"✅ 테스트 메일 발송 성공!")
        
        # 연결 종료
        server.quit()
        
        print(f"🎉 모든 테스트 완료!")
        return True
        
    except socket.timeout:
        print(f"❌ 연결 타임아웃: {smtp_host}:{smtp_port}")
        return False
    except ConnectionRefusedError:
        print(f"❌ 연결 거부: {smtp_host}:{smtp_port}")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False

if __name__ == "__main__":
    print("🚀 SkyBoot Mail WSL Postfix SMTP 테스트")
    print("=" * 60)
    
    success = test_smtp_connection()
    
    if success:
        print("\n🎊 테스트 성공! WSL Postfix SMTP 서버가 정상 작동합니다.")
        sys.exit(0)
    else:
        print("\n💥 테스트 실패! SMTP 서버 연결에 문제가 있습니다.")
        sys.exit(1)