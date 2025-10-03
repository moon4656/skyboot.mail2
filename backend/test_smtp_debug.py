#!/usr/bin/env python3
"""
SMTP 연결 디버깅 스크립트
FastAPI 애플리케이션의 SMTP 연결 과정을 상세히 추적합니다.
"""

import requests
import json
import time
from datetime import datetime

def test_smtp_with_debug():
    """SMTP 발송을 테스트하고 상세한 디버깅 정보를 출력합니다."""
    print("🔧 SMTP 디버깅 테스트")
    print("=" * 60)
    
    # 1. 로그인
    print("🔐 사용자 로그인 중...")
    login_data = {
        "user_id": "admin01",
        "password": "test"
    }
    
    login_response = requests.post(
        "http://localhost:8000/api/v1/auth/login",
        json=login_data
    )
    
    if login_response.status_code != 200:
        print(f"❌ 로그인 실패: {login_response.status_code}")
        print(f"응답: {login_response.text}")
        return False, None, None
    
    token = login_response.json()["access_token"]
    print(f"✅ 로그인 성공!")
    
    # 2. 메일 발송 전 시간 기록
    send_time = datetime.now()
    print(f"📅 메일 발송 시작 시간: {send_time.strftime('%H:%M:%S')}")
    
    # 3. 메일 발송
    print("\n📤 테스트 메일 발송 중...")
    headers = {"Authorization": f"Bearer {token}"}
    
    mail_data = {
        "to_emails": "moon4656@gmail.com",
        "subject": f"SMTP 디버깅 테스트 - {send_time.strftime('%H:%M:%S')}",
        "content": f"""이 메일은 SMTP 연결 디버깅을 위해 발송되었습니다.

발송 시간: {send_time.strftime('%Y-%m-%d %H:%M:%S')}
테스트 목적: FastAPI → Postfix SMTP 연결 확인

만약 이 메일을 받으셨다면, SMTP 연결이 정상적으로 작동하고 있습니다."""
    }
    
    print(f"📧 수신자: {mail_data['to_emails']}")
    print(f"📝 제목: {mail_data['subject']}")
    
    # 메일 발송 요청 (Form 데이터 사용)
    mail_response = requests.post(
        "http://localhost:8000/api/v1/mail/send",
        data=mail_data,
        headers=headers
    )
    
    print(f"\n📊 응답 상태: {mail_response.status_code}")
    
    if mail_response.status_code == 200:
        response_data = mail_response.json()
        print(f"📄 응답 내용: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        
        mail_uuid = response_data.get('mail_uuid')
        sent_at = response_data.get('sent_at')
        
        print(f"\n✅ 메일 발송 API 성공!")
        print(f"   - 메일 UUID: {mail_uuid}")
        print(f"   - 발송 시간: {sent_at}")
        
        # 4. 잠시 대기 후 Postfix 로그 확인
        print(f"\n⏳ 3초 대기 후 Postfix 로그 확인...")
        time.sleep(3)
        
        return True, send_time, mail_uuid
        
    else:
        print(f"❌ 메일 발송 실패: {mail_response.status_code}")
        print(f"응답: {mail_response.text}")
        return False, send_time, None

def check_postfix_logs(send_time, mail_uuid):
    """Postfix 로그에서 해당 메일을 찾습니다."""
    print("\n🔍 Postfix 로그 확인 중...")
    
    # 발송 시간 기준으로 로그 검색
    time_str = send_time.strftime("%H:%M")
    
    import subprocess
    
    try:
        # 최근 로그에서 해당 시간대 검색
        cmd = f'wsl bash -c "tail -n 100 /var/log/mail.log | grep -E \'({time_str}|moon4656@gmail.com)\'"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            print("✅ Postfix 로그에서 관련 항목 발견:")
            print(result.stdout)
            return True
        else:
            print("❌ Postfix 로그에서 해당 시간대의 메일을 찾을 수 없습니다.")
            
            # 전체 최근 로그 확인
            cmd2 = 'wsl bash -c "tail -n 20 /var/log/mail.log"'
            result2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
            
            if result2.returncode == 0:
                print("\n📋 최근 Postfix 로그 (마지막 20줄):")
                print(result2.stdout)
            
            return False
            
    except Exception as e:
        print(f"❌ 로그 확인 중 오류: {e}")
        return False

if __name__ == "__main__":
    print("🚀 SMTP 디버깅 테스트 시작")
    print("=" * 60)
    
    success, send_time, mail_uuid = test_smtp_with_debug()
    
    if success:
        postfix_found = check_postfix_logs(send_time, mail_uuid)
        
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약:")
        print(f"   - FastAPI 메일 발송 API: ✅ 성공")
        print(f"   - Postfix 로그 기록: {'✅ 발견' if postfix_found else '❌ 없음'}")
        
        if not postfix_found:
            print("\n💡 분석:")
            print("   - FastAPI에서는 메일 발송이 성공했다고 응답")
            print("   - 하지만 Postfix 로그에는 기록되지 않음")
            print("   - 이는 FastAPI가 실제로 SMTP 서버에 연결하지 못했음을 의미")
            print("   - SMTP 설정이나 연결 로직에 문제가 있을 가능성")
        else:
            print("\n🎉 모든 테스트 통과!")
            print("   - FastAPI와 Postfix SMTP 연결이 정상 작동")
    else:
        print("\n❌ FastAPI 메일 발송 API 자체가 실패했습니다.")
    
    print("\n📬 테스트 완료!")
    print("📧 moon4656@gmail.com 메일함을 확인해보세요.")