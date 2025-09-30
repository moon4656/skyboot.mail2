#!/usr/bin/env python3
"""
Gmail SMTP 인증 설정 스크립트
"""

def setup_gmail_auth():
    """Gmail 앱 비밀번호 설정 가이드"""
    
    print("🔧 Gmail SMTP 인증 설정 가이드")
    print("=" * 50)
    
    print("\n1️⃣ Gmail 앱 비밀번호 생성:")
    print("   - Gmail 계정 설정 → 보안 → 2단계 인증 활성화")
    print("   - 앱 비밀번호 생성 (앱: 메일, 기기: 기타)")
    print("   - 16자리 앱 비밀번호 복사")
    
    print("\n2️⃣ 앱 비밀번호 입력:")
    app_password = input("   Gmail 앱 비밀번호를 입력하세요 (16자리): ").strip()
    
    if len(app_password) != 16:
        print("   ❌ 앱 비밀번호는 16자리여야 합니다.")
        return False
    
    # sasl_passwd 파일 업데이트
    sasl_content = f"[smtp.gmail.com]:587 skyboot.mail.service@gmail.com:{app_password}\n"
    
    try:
        with open("../postfix_sasl_passwd", "w", encoding="utf-8") as f:
            f.write(sasl_content)
        
        print("   ✅ postfix_sasl_passwd 파일 업데이트 완료")
        
        print("\n3️⃣ 다음 단계:")
        print("   1. WSL에서 다음 명령어 실행:")
        print("      sudo cp postfix_sasl_passwd /etc/postfix/sasl_passwd")
        print("      sudo postmap /etc/postfix/sasl_passwd")
        print("      sudo chmod 600 /etc/postfix/sasl_passwd*")
        print("      sudo cp postfix_main.cf /etc/postfix/main.cf")
        print("      sudo postfix reload")
        
        print("\n   2. 메일 재전송 테스트:")
        print("      python test/send_test_email.py")
        
        print("\n✅ 설정 파일 준비 완료!")
        return True
        
    except Exception as e:
        print(f"   ❌ 파일 업데이트 실패: {e}")
        return False

if __name__ == "__main__":
    setup_gmail_auth()