#!/usr/bin/env python3
"""
SASL 설정 적용 및 검증 스크립트
Gmail SMTP 릴레이를 위한 Postfix SASL 클라이언트 설정을 WSL에 적용합니다.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_wsl_command(command, description):
    """WSL 명령어를 실행하고 결과를 반환합니다."""
    print(f"\n🔧 {description}")
    print(f"실행: {command}")
    
    try:
        result = subprocess.run(
            f"wsl {command}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ 성공: {description}")
            if result.stdout.strip():
                print(f"출력: {result.stdout.strip()}")
        else:
            print(f"❌ 실패: {description}")
            print(f"에러: {result.stderr.strip()}")
            
        return result.returncode == 0, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        print(f"⏰ 타임아웃: {description}")
        return False, "", "명령어 실행 시간 초과"
    except Exception as e:
        print(f"💥 예외 발생: {e}")
        return False, "", str(e)

def check_app_password():
    """앱 비밀번호가 설정되었는지 확인합니다."""
    print("\n📋 Gmail 앱 비밀번호 확인")
    
    sasl_file = Path("postfix_sasl_passwd")
    if not sasl_file.exists():
        print("❌ postfix_sasl_passwd 파일이 없습니다.")
        return False
    
    content = sasl_file.read_text(encoding='utf-8')
    if "YOUR_APP_PASSWORD_HERE" in content:
        print("⚠️ Gmail 앱 비밀번호가 아직 설정되지 않았습니다.")
        print("📝 다음 단계를 완료하세요:")
        print("1. https://myaccount.google.com/ → 보안")
        print("2. 2단계 인증 활성화")
        print("3. 앱 비밀번호 생성 → 'SkyBoot Mail Server'")
        print("4. postfix_sasl_passwd 파일에서 YOUR_APP_PASSWORD_HERE를 실제 앱 비밀번호로 교체")
        return False
    
    print("✅ Gmail 앱 비밀번호가 설정되어 있습니다.")
    return True

def apply_sasl_settings():
    """SASL 설정을 WSL 환경에 적용합니다."""
    print("\n🚀 SASL 설정 적용 시작")
    
    # 1. 설정 파일 복사
    commands = [
        ("sudo cp postfix_main.cf /etc/postfix/main.cf", "Postfix 메인 설정 복사"),
        ("sudo cp postfix_sasl_passwd /etc/postfix/sasl_passwd", "SASL 인증 파일 복사"),
        ("sudo chmod 600 /etc/postfix/sasl_passwd", "SASL 파일 권한 설정"),
        ("sudo postmap /etc/postfix/sasl_passwd", "SASL 패스워드 맵 생성"),
        ("sudo systemctl reload postfix", "Postfix 설정 다시 로드"),
        ("sudo systemctl status postfix --no-pager -l", "Postfix 상태 확인")
    ]
    
    success_count = 0
    for command, description in commands:
        success, stdout, stderr = run_wsl_command(command, description)
        if success:
            success_count += 1
        else:
            print(f"⚠️ 명령어 실패, 계속 진행합니다: {command}")
    
    print(f"\n📊 설정 적용 결과: {success_count}/{len(commands)} 성공")
    return success_count == len(commands)

def test_smtp_connection():
    """Gmail SMTP 연결을 테스트합니다."""
    print("\n🧪 Gmail SMTP 연결 테스트")
    
    test_script = '''
import smtplib
import ssl
from email.mime.text import MIMEText

def test_gmail_smtp():
    try:
        # Gmail SMTP 서버 연결
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        
        # 인증 정보 읽기
        with open("/etc/postfix/sasl_passwd", "r") as f:
            for line in f:
                if line.startswith("[smtp.gmail.com]:587"):
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        auth_info = parts[1].split(":")
                        if len(auth_info) >= 2:
                            username = auth_info[0]
                            password = ":".join(auth_info[1:])
                            
                            print(f"사용자명: {username}")
                            print("비밀번호: [보안상 숨김]")
                            
                            # 로그인 테스트
                            server.login(username, password)
                            print("✅ Gmail SMTP 인증 성공!")
                            server.quit()
                            return True
        
        print("❌ 인증 정보를 찾을 수 없습니다.")
        return False
        
    except Exception as e:
        print(f"❌ Gmail SMTP 연결 실패: {e}")
        return False

if __name__ == "__main__":
    test_gmail_smtp()
'''
    
    # 테스트 스크립트를 임시 파일로 저장
    with open("temp_smtp_test.py", "w", encoding="utf-8") as f:
        f.write(test_script)
    
    # WSL에서 테스트 실행
    success, stdout, stderr = run_wsl_command(
        "python3 temp_smtp_test.py", 
        "Gmail SMTP 연결 테스트"
    )
    
    # 임시 파일 삭제
    try:
        os.remove("temp_smtp_test.py")
    except:
        pass
    
    return success

def main():
    """메인 실행 함수"""
    print("🔧 SkyBoot Mail - SASL 설정 적용 도구")
    print("=" * 50)
    
    # 1. 앱 비밀번호 확인
    if not check_app_password():
        print("\n❌ Gmail 앱 비밀번호를 먼저 설정해주세요.")
        return False
    
    # 2. SASL 설정 적용
    if not apply_sasl_settings():
        print("\n❌ SASL 설정 적용에 실패했습니다.")
        return False
    
    # 3. SMTP 연결 테스트
    if test_smtp_connection():
        print("\n🎉 SASL 설정이 성공적으로 적용되었습니다!")
        print("📧 이제 Gmail SMTP 릴레이를 통해 메일을 발송할 수 있습니다.")
    else:
        print("\n⚠️ SASL 설정은 적용되었지만 SMTP 연결 테스트에 실패했습니다.")
        print("📝 Gmail 앱 비밀번호를 다시 확인해주세요.")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n💥 예상치 못한 오류: {e}")
        sys.exit(1)