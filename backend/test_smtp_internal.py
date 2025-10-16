#!/usr/bin/env python3
"""
WSL 내부에서 실행할 SMTP 연결 테스트
"""
import smtplib
import socket
import sys

def test_smtp_internal():
    """WSL 내부에서 localhost SMTP 테스트"""
    
    print("🔍 WSL 내부 SMTP 테스트 시작")
    print("📍 서버: localhost:25")
    print("-" * 40)
    
    try:
        # 1. 소켓 연결 테스트
        print("1️⃣ 소켓 연결 테스트...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', 25))
        
        if result == 0:
            print("✅ 소켓 연결 성공")
            sock.close()
        else:
            print(f"❌ 소켓 연결 실패: {result}")
            return False
            
        # 2. SMTP 연결 테스트
        print("2️⃣ SMTP 연결 테스트...")
        
        server = smtplib.SMTP(timeout=5)
        server.set_debuglevel(1)
        
        print("📡 SMTP 서버 연결...")
        server.connect('localhost', 25)
        
        print("👋 EHLO 명령...")
        server.ehlo()
        
        print("✅ SMTP 연결 성공!")
        
        # 연결 종료
        server.quit()
        
        print("🎉 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False

if __name__ == "__main__":
    success = test_smtp_internal()
    sys.exit(0 if success else 1)