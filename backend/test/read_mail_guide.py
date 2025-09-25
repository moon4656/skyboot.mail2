#!/usr/bin/env python3
"""
WSL에서 메일을 읽는 방법 가이드
"""

import subprocess
import sys
from datetime import datetime

def show_mailbox_list():
    """
    사용 가능한 메일박스 목록 표시
    """
    print("=" * 60)
    print("📬 사용 가능한 메일박스 목록")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ['wsl', 'ls', '-la', '/var/spool/mail/'], 
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            print("📋 메일박스 목록:")
            for line in lines[2:]:  # 첫 두 줄은 . 과 .. 디렉토리
                if line.strip() and not line.startswith('total'):
                    parts = line.split()
                    if len(parts) >= 9:
                        filename = parts[-1]
                        size = parts[4]
                        modified = ' '.join(parts[5:8])
                        print(f"   📧 {filename}: {size} bytes (수정: {modified})")
        else:
            print(f"❌ 메일박스 목록 확인 실패: {result.stderr}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

def read_mail_with_cat(username):
    """
    cat 명령어로 메일 읽기
    """
    print(f"\n=" * 60)
    print(f"📖 {username} 메일박스 내용 (cat 명령어)")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ['wsl', 'cat', f'/var/spool/mail/{username}'], 
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            content = result.stdout
            if content.strip():
                print(f"📧 {username}의 메일 내용:\n")
                print(content)
            else:
                print(f"📭 {username}의 메일박스가 비어있습니다.")
        else:
            print(f"❌ {username} 메일박스를 읽을 수 없습니다: {result.stderr}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

def read_mail_with_tail(username, lines=10):
    """
    tail 명령어로 최근 메일 읽기
    """
    print(f"\n=" * 60)
    print(f"📖 {username} 최근 메일 {lines}줄 (tail 명령어)")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ['wsl', 'tail', f'-{lines}', f'/var/spool/mail/{username}'], 
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            content = result.stdout
            if content.strip():
                print(f"📧 {username}의 최근 메일 {lines}줄:\n")
                print(content)
            else:
                print(f"📭 {username}의 메일박스가 비어있습니다.")
        else:
            print(f"❌ {username} 메일박스를 읽을 수 없습니다: {result.stderr}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

def count_mails(username):
    """
    메일 개수 세기
    """
    print(f"\n=" * 60)
    print(f"📊 {username} 메일 개수 확인")
    print("=" * 60)
    
    try:
        # From 라인 개수로 메일 개수 계산
        result = subprocess.run(
            ['wsl', 'grep', '-c', '^From ', f'/var/spool/mail/{username}'], 
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            count = result.stdout.strip()
            print(f"📧 {username}의 총 메일 개수: {count}개")
            
            # 메일박스 크기도 확인
            size_result = subprocess.run(
                ['wsl', 'wc', '-c', f'/var/spool/mail/{username}'], 
                capture_output=True, text=True, timeout=10
            )
            
            if size_result.returncode == 0:
                size = size_result.stdout.strip().split()[0]
                print(f"📦 메일박스 크기: {size} bytes")
                
        else:
            print(f"❌ {username} 메일 개수를 확인할 수 없습니다: {result.stderr}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

def show_mail_headers(username):
    """
    메일 헤더만 표시
    """
    print(f"\n=" * 60)
    print(f"📋 {username} 메일 헤더 목록")
    print("=" * 60)
    
    try:
        # From, Subject, Date 헤더만 추출
        result = subprocess.run(
            ['wsl', 'grep', '-E', '^(From |Subject:|Date:)', f'/var/spool/mail/{username}'], 
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            headers = result.stdout.strip()
            if headers:
                print(f"📧 {username}의 메일 헤더:\n")
                print(headers)
            else:
                print(f"📭 {username}의 메일박스가 비어있습니다.")
        else:
            print(f"❌ {username} 메일 헤더를 읽을 수 없습니다: {result.stderr}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

def interactive_mail_reader():
    """
    대화형 메일 리더 (비차단 방식)
    """
    print(f"\n=" * 60)
    print(f"📖 대화형 메일 리더 사용법")
    print("=" * 60)
    
    print("🔧 WSL에서 대화형으로 메일을 읽는 방법:")
    print("")
    print("1. 기본 mail 명령어:")
    print("   wsl mail -u eldorado")
    print("   - 메일 목록이 표시됩니다")
    print("   - 숫자를 입력하여 특정 메일 읽기")
    print("   - 'q'를 입력하여 종료")
    print("")
    print("2. 메일 목록만 보기:")
    print("   wsl mail -u eldorado -H")
    print("")
    print("3. 특정 메일 번호 읽기:")
    print("   wsl mail -u eldorado -p 1")
    print("")
    print("4. 새 메일만 보기:")
    print("   wsl mail -u eldorado -N")
    print("")
    print("5. 메일 삭제:")
    print("   wsl mail -u eldorado")
    print("   메일 번호 입력 후 'd' 명령어 사용")
    print("")
    print("⚠️ 주의: 대화형 명령어는 PowerShell에서 직접 실행하세요!")

def create_test_user_mail():
    """
    testuser에게 테스트 메일 발송
    """
    print(f"\n=" * 60)
    print(f"📤 testuser에게 테스트 메일 발송")
    print("=" * 60)
    
    try:
        # testuser 시스템 사용자가 있는지 확인
        user_check = subprocess.run(
            ['wsl', 'id', 'testuser'], 
            capture_output=True, text=True, timeout=10
        )
        
        if user_check.returncode != 0:
            print("⚠️ testuser 시스템 사용자가 없습니다.")
            print("🔧 testuser 생성 방법:")
            print("   wsl sudo useradd -m testuser")
            print("   wsl sudo passwd testuser")
            return
        
        # 메일 발송
        mail_content = f"""
안녕하세요 testuser님!

이것은 {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}에 발송된 테스트 메일입니다.

메일 읽기 테스트를 위해 발송되었습니다.

감사합니다.
SkyBoot Mail System
        """
        
        result = subprocess.run(
            ['wsl', 'sh', '-c', f'echo "{mail_content}" | mail -s "testuser 메일 읽기 테스트" testuser@localhost'], 
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0:
            print("✅ testuser에게 테스트 메일을 발송했습니다!")
            print("📋 이제 다음 명령어로 메일을 확인할 수 있습니다:")
            print("   wsl cat /var/spool/mail/testuser")
            print("   wsl mail -u testuser")
        else:
            print(f"❌ 메일 발송 실패: {result.stderr}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

def main():
    """
    메인 함수
    """
    print("🚀 WSL 메일 읽기 가이드")
    print(f"⏰ 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 메일박스 목록 표시
    show_mailbox_list()
    
    # 2. eldorado 메일 읽기 (여러 방법)
    read_mail_with_tail('eldorado', 20)
    count_mails('eldorado')
    show_mail_headers('eldorado')
    
    # 3. user01 메일도 확인
    count_mails('user01')
    
    # 4. testuser 메일 생성 및 읽기
    create_test_user_mail()
    
    # 5. 대화형 메일 리더 사용법
    interactive_mail_reader()
    
    print("\n" + "=" * 60)
    print("📚 메일 읽기 방법 요약")
    print("=" * 60)
    print("1. 📖 전체 메일 내용: wsl cat /var/spool/mail/사용자명")
    print("2. 📋 최근 메일: wsl tail -20 /var/spool/mail/사용자명")
    print("3. 📊 메일 개수: wsl grep -c '^From ' /var/spool/mail/사용자명")
    print("4. 📧 대화형 읽기: wsl mail -u 사용자명")
    print("5. 🔍 헤더만 보기: wsl grep -E '^(From |Subject:|Date:)' /var/spool/mail/사용자명")
    
    print(f"\n⏰ 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()