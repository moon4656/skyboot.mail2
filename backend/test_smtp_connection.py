#!/usr/bin/env python3
"""
SMTP 서버 연결 테스트 스크립트
FastAPI 애플리케이션이 실제로 SMTP 서버에 연결할 수 있는지 확인합니다.
"""

import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def test_smtp_connection():
    """SMTP 서버 연결 테스트"""
    print("🔧 SMTP 서버 연결 테스트")
    print("=" * 50)
    
    # 환경 변수에서 SMTP 설정 읽기
    smtp_host = os.getenv('SMTP_HOST', 'localhost')
    smtp_port = int(os.getenv('SMTP_PORT', '25'))
    smtp_user = os.getenv('SMTP_USERNAME', '')
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    
    print(f"📡 SMTP 호스트: {smtp_host}")
    print(f"🔌 SMTP 포트: {smtp_port}")
    print(f"👤 SMTP 사용자: {smtp_user if smtp_user else '(없음)'}")
    print(f"🔑 SMTP 비밀번호: {'설정됨' if smtp_password else '(없음)'}")
    print()
    
    # 1. 포트 연결 테스트
    print("1️⃣ 포트 연결 테스트...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((smtp_host, smtp_port))
        sock.close()
        
        if result == 0:
            print(f"✅ {smtp_host}:{smtp_port} 포트 연결 성공")
        else:
            print(f"❌ {smtp_host}:{smtp_port} 포트 연결 실패 (에러 코드: {result})")
            return False
    except Exception as e:
        print(f"❌ 포트 연결 테스트 실패: {e}")
        return False
    
    # 2. SMTP 서버 연결 테스트
    print("\n2️⃣ SMTP 서버 연결 테스트...")
    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.set_debuglevel(1)  # 디버그 모드 활성화
        
        print("✅ SMTP 서버 연결 성공")
        
        # EHLO 명령 테스트
        print("\n3️⃣ EHLO 명령 테스트...")
        server.ehlo()
        print("✅ EHLO 명령 성공")
        
        # TLS 지원 확인
        print("\n4️⃣ TLS 지원 확인...")
        if server.has_extn('STARTTLS'):
            print("✅ STARTTLS 지원됨")
            try:
                server.starttls()
                print("✅ TLS 연결 성공")
            except Exception as e:
                print(f"⚠️ TLS 연결 실패: {e}")
        else:
            print("ℹ️ STARTTLS 지원되지 않음 (일반 연결 사용)")
        
        # 인증 테스트 (사용자명/비밀번호가 있는 경우)
        if smtp_user and smtp_password:
            print("\n5️⃣ SMTP 인증 테스트...")
            try:
                server.login(smtp_user, smtp_password)
                print("✅ SMTP 인증 성공")
            except Exception as e:
                print(f"❌ SMTP 인증 실패: {e}")
                server.quit()
                return False
        else:
            print("\n5️⃣ SMTP 인증 건너뜀 (사용자명/비밀번호 없음)")
        
        # 테스트 메일 발송
        print("\n6️⃣ 테스트 메일 발송...")
        try:
            msg = MIMEMultipart()
            msg['From'] = 'test@skyboot.local'
            msg['To'] = 'moon4656@gmail.com'
            msg['Subject'] = 'SMTP 연결 테스트 메일'
            
            body = """
이 메일은 SMTP 서버 연결 테스트를 위해 발송되었습니다.

테스트 시간: {timestamp}
SMTP 서버: {host}:{port}
""".format(
                timestamp=__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                host=smtp_host,
                port=smtp_port
            )
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            text = msg.as_string()
            server.sendmail('test@skyboot.local', 'moon4656@gmail.com', text)
            print("✅ 테스트 메일 발송 성공")
            
        except Exception as e:
            print(f"❌ 테스트 메일 발송 실패: {e}")
            server.quit()
            return False
        
        server.quit()
        print("\n✅ 모든 SMTP 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ SMTP 서버 연결 실패: {e}")
        return False

if __name__ == "__main__":
    success = test_smtp_connection()
    if success:
        print("\n🎉 SMTP 서버가 정상적으로 작동하고 있습니다!")
        print("📬 moon4656@gmail.com 메일함을 확인해보세요.")
    else:
        print("\n💥 SMTP 서버 연결에 문제가 있습니다.")
        print("🔧 설정을 확인하고 다시 시도해주세요.")