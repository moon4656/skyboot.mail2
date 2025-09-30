#!/usr/bin/env python3
"""
Gmail SMTP 연결 직접 테스트 스크립트
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_gmail_smtp():
    """Gmail SMTP 서버에 직접 연결하여 메일 전송 테스트"""
    
    # Gmail SMTP 설정
    smtp_server = "smtp.gmail.com"
    port = 587
    sender_email = "skyboot.mail.service@gmail.com"
    password = "safe70!!"  # 실제로는 앱 비밀번호를 사용해야 함
    receiver_email = "moon4656@gmail.com"
    
    print("🔗 Gmail SMTP 직접 연결 테스트 시작")
    print("=" * 50)
    
    try:
        # 메일 메시지 생성
        message = MIMEMultipart("alternative")
        message["Subject"] = "SkyBoot Mail - 직접 SMTP 테스트"
        message["From"] = sender_email
        message["To"] = receiver_email
        
        # 메일 본문
        text = """
        안녕하세요!
        
        이것은 SkyBoot Mail 시스템에서 Gmail SMTP를 통해 직접 전송하는 테스트 메일입니다.
        
        만약 이 메일을 받으셨다면, Gmail SMTP 연결이 정상적으로 작동하고 있는 것입니다.
        
        감사합니다.
        SkyBoot Mail 팀
        """
        
        html = """
        <html>
          <body>
            <h2>SkyBoot Mail SMTP 테스트</h2>
            <p>안녕하세요!</p>
            <p>이것은 SkyBoot Mail 시스템에서 Gmail SMTP를 통해 직접 전송하는 테스트 메일입니다.</p>
            <p>만약 이 메일을 받으셨다면, <strong>Gmail SMTP 연결이 정상적으로 작동</strong>하고 있는 것입니다.</p>
            <br>
            <p>감사합니다.<br>
            <em>SkyBoot Mail 팀</em></p>
          </body>
        </html>
        """
        
        # 텍스트와 HTML 버전 추가
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        message.attach(part1)
        message.attach(part2)
        
        print(f"📧 메일 생성 완료")
        print(f"   - 발신자: {sender_email}")
        print(f"   - 수신자: {receiver_email}")
        print(f"   - 제목: {message['Subject']}")
        
        # SMTP 서버 연결
        print(f"\n🔌 Gmail SMTP 서버 연결 중...")
        print(f"   - 서버: {smtp_server}")
        print(f"   - 포트: {port}")
        
        context = ssl.create_default_context()
        server = smtplib.SMTP(smtp_server, port)
        
        print("✅ SMTP 서버 연결 성공")
        
        # TLS 시작
        print("🔒 TLS 암호화 시작...")
        server.starttls(context=context)
        print("✅ TLS 암호화 성공")
        
        # 로그인
        print("🔑 Gmail 계정 로그인 중...")
        server.login(sender_email, password)
        print("✅ Gmail 로그인 성공")
        
        # 메일 전송
        print("📤 메일 전송 중...")
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        print("✅ 메일 전송 성공!")
        
        # 연결 종료
        server.quit()
        print("🔌 SMTP 연결 종료")
        
        print("\n" + "=" * 50)
        print("✅ Gmail SMTP 직접 테스트 완료!")
        print("📬 moon4656@gmail.com 메일함을 확인해보세요.")
        print("📝 메일이 스팸함에 들어갈 수 있으니 스팸함도 확인해주세요.")
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Gmail 인증 실패: {e}")
        print("💡 Gmail 앱 비밀번호가 올바른지 확인해주세요.")
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP 오류: {e}")
        
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    test_gmail_smtp()