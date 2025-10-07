#!/usr/bin/env python3
"""
SMTP 직접 연결 테스트 스크립트
메일 서비스에서 사용하는 것과 동일한 SMTP 설정으로 직접 메일 발송을 테스트합니다.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def test_smtp_direct():
    """SMTP 직접 연결 및 메일 발송 테스트"""
    
    # SMTP 설정 (mail_service.py와 동일)
    smtp_server = os.getenv('SMTP_HOST', 'localhost')
    smtp_port = int(os.getenv('SMTP_PORT', '25'))
    smtp_username = os.getenv('SMTP_USERNAME', '')
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    use_tls = os.getenv('SMTP_USE_TLS', 'false').lower() == 'true'
    
    print(f"🔧 SMTP 설정:")
    print(f"   서버: {smtp_server}:{smtp_port}")
    print(f"   사용자명: {smtp_username if smtp_username else '(없음)'}")
    print(f"   비밀번호: {'설정됨' if smtp_password else '(없음)'}")
    print(f"   TLS 사용: {use_tls}")
    print()
    
    # 테스트 메일 데이터
    sender_email = "test@skyboot.local"
    recipient_email = "moon4656@gmail.com"
    subject = "SMTP 직접 테스트 메일"
    body = "이것은 SMTP 직접 연결 테스트 메일입니다."
    
    try:
        print("1️⃣ SMTP 서버 연결 시도...")
        
        # SMTP 서버 연결
        if use_tls:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            print("✅ TLS 연결 성공")
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            print("✅ 일반 연결 성공")
        
        # 인증 (사용자명과 비밀번호가 있는 경우)
        if smtp_username and smtp_password:
            print("2️⃣ SMTP 인증 시도...")
            server.login(smtp_username, smtp_password)
            print("✅ SMTP 인증 성공")
        else:
            print("2️⃣ SMTP 인증 건너뜀 (사용자명/비밀번호 없음)")
        
        # 메일 메시지 생성
        print("3️⃣ 메일 메시지 생성...")
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # 본문 추가
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 메일 발송
        print("4️⃣ 메일 발송 시도...")
        text = msg.as_string()
        result = server.sendmail(sender_email, [recipient_email], text)
        
        print("✅ 메일 발송 성공!")
        print(f"   발송자: {sender_email}")
        print(f"   수신자: {recipient_email}")
        print(f"   제목: {subject}")
        
        if result:
            print(f"   발송 결과: {result}")
        else:
            print("   모든 수신자에게 성공적으로 발송됨")
        
        # 연결 종료
        server.quit()
        print("✅ SMTP 연결 종료")
        
        return True
        
    except smtplib.SMTPConnectError as e:
        print(f"❌ SMTP 연결 오류: {e}")
        return False
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP 인증 오류: {e}")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        print(f"❌ 수신자 거부 오류: {e}")
        return False
    except smtplib.SMTPSenderRefused as e:
        print(f"❌ 발송자 거부 오류: {e}")
        return False
    except smtplib.SMTPDataError as e:
        print(f"❌ SMTP 데이터 오류: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ 일반 SMTP 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        import traceback
        print(f"❌ 상세 스택 트레이스:")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("🧪 SMTP 직접 연결 테스트 시작")
    print("=" * 50)
    
    success = test_smtp_direct()
    
    print("=" * 50)
    if success:
        print("🎉 SMTP 테스트 성공!")
    else:
        print("💥 SMTP 테스트 실패!")