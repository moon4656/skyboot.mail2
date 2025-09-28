#!/usr/bin/env python3
"""
간단한 메일 발송 테스트 스크립트
SMTP 연결 문제를 진단하고 해결합니다.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def test_smtp_connection():
    """SMTP 연결 테스트"""
    print("🔧 SMTP 연결 테스트 시작...")
    
    # 다양한 SMTP 설정 테스트
    smtp_configs = [
        {"host": "localhost", "port": 25, "name": "로컬 Postfix (포트 25)"},
        {"host": "localhost", "port": 587, "name": "로컬 Postfix (포트 587)"},
        {"host": "127.0.0.1", "port": 25, "name": "로컬호스트 (포트 25)"},
        {"host": "127.0.0.1", "port": 587, "name": "로컬호스트 (포트 587)"},
    ]
    
    working_config = None
    
    for config in smtp_configs:
        try:
            print(f"\n📡 {config['name']} 연결 테스트...")
            with smtplib.SMTP(config["host"], config["port"], timeout=10) as server:
                server.ehlo()
                print(f"✅ {config['name']} 연결 성공!")
                working_config = config
                break
        except Exception as e:
            print(f"❌ {config['name']} 연결 실패: {str(e)}")
    
    return working_config

def send_simple_mail(smtp_config):
    """간단한 메일 발송 테스트"""
    if not smtp_config:
        print("❌ 사용 가능한 SMTP 설정이 없습니다.")
        return False
    
    try:
        print(f"\n📧 메일 발송 테스트 ({smtp_config['name']})...")
        
        # 메일 메시지 생성
        msg = MIMEMultipart()
        msg['From'] = "test@skyboot.local"
        msg['To'] = "mailtest@example.com"
        msg['Subject'] = f"테스트 메일 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        body = f"""
안녕하세요!

이것은 메일 발송 테스트입니다.

발송 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분 %S초')}
SMTP 서버: {smtp_config['host']}:{smtp_config['port']}

테스트가 성공적으로 완료되었습니다.

감사합니다.
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # SMTP 서버를 통해 메일 발송
        with smtplib.SMTP(smtp_config["host"], smtp_config["port"], timeout=30) as server:
            server.send_message(msg)
            
        print(f"✅ 메일 발송 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 메일 발송 실패: {str(e)}")
        return False

def main():
    """메인 함수"""
    print("=" * 60)
    print("📧 간단한 메일 발송 테스트")
    print("=" * 60)
    
    # SMTP 연결 테스트
    working_config = test_smtp_connection()
    
    if working_config:
        print(f"\n🎉 사용 가능한 SMTP 설정: {working_config['name']}")
        
        # 메일 발송 테스트
        success = send_simple_mail(working_config)
        
        if success:
            print("\n✅ 모든 테스트가 성공적으로 완료되었습니다!")
            print(f"   권장 SMTP 설정: {working_config['host']}:{working_config['port']}")
        else:
            print("\n❌ 메일 발송 테스트가 실패했습니다.")
    else:
        print("\n❌ 사용 가능한 SMTP 서버를 찾을 수 없습니다.")
        print("   Postfix가 설치되어 있고 실행 중인지 확인해주세요.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()