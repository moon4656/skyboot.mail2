#!/usr/bin/env python3
"""
휴지통 메일 조회 API 테스트 - 실제 데이터 생성 및 테스트
user01 계정으로 메일을 생성하고 휴지통으로 이동시켜 테스트
"""

import requests
import json
from datetime import datetime
import time

# 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def login_user(user_id, password):
    """사용자 로그인"""
    login_data = {
        "user_id": user_id,
        "password": password
    }
    
    login_response = requests.post(
        f"{BASE_URL}{API_PREFIX}/auth/login",
        json=login_data
    )
    
    if login_response.status_code == 200:
        login_result = login_response.json()
        access_token = login_result.get("access_token")
        return access_token
    else:
        print(f"❌ {user_id} 로그인 실패: {login_response.text}")
        return None

def create_test_mail(headers, subject, content, is_draft=False):
    """테스트 메일 생성"""
    mail_data = {
        "recipients": ["test@example.com"],
        "subject": subject,
        "content": content,
        "is_draft": is_draft
    }
    
    mail_response = requests.post(
        f"{BASE_URL}{API_PREFIX}/mail/send",
        json=mail_data,
        headers=headers
    )
    
    if mail_response.status_code == 200:
        result = mail_response.json()
        return result.get("data", {}).get("mail_uuid")
    else:
        print(f"❌ 메일 생성 실패: {mail_response.text}")
        return None

def test_trash_with_data():
    """실제 데이터로 휴지통 API 테스트"""
    print("🗑️ 휴지통 메일 조회 API 테스트 (실제 데이터)")
    print(f"⏰ 테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. user01 로그인
    print("\n🔐 user01 로그인 중...")
    access_token = login_user("user01", "test")
    
    if not access_token:
        print("❌ 로그인 실패로 테스트를 중단합니다.")
        return
    
    print("✅ 로그인 성공!")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 2. 테스트 메일 생성 (임시보관함)
    print("\n📝 테스트 메일 생성 중...")
    
    test_mails = [
        {
            "subject": "휴지통 테스트 메일 1 - 임시보관함",
            "content": "이 메일은 휴지통 테스트를 위한 임시보관함 메일입니다.",
            "is_draft": True
        },
        {
            "subject": "휴지통 테스트 메일 2 - 발송 메일",
            "content": "이 메일은 휴지통 테스트를 위한 발송 메일입니다.",
            "is_draft": False
        },
        {
            "subject": "휴지통 테스트 메일 3 - 임시보관함",
            "content": "이 메일은 휴지통 테스트를 위한 또 다른 임시보관함 메일입니다.",
            "is_draft": True
        }
    ]
    
    created_mails = []
    for mail_info in test_mails:
        mail_uuid = create_test_mail(
            headers, 
            mail_info["subject"], 
            mail_info["content"], 
            mail_info["is_draft"]
        )
        
        if mail_uuid:
            created_mails.append({
                "uuid": mail_uuid,
                "subject": mail_info["subject"],
                "is_draft": mail_info["is_draft"]
            })
            print(f"✅ 메일 생성 성공: {mail_info['subject']} (UUID: {mail_uuid})")
        else:
            print(f"❌ 메일 생성 실패: {mail_info['subject']}")
    
    print(f"\n📊 총 {len(created_mails)}개의 테스트 메일이 생성되었습니다.")
    
    # 3. 임시보관함 조회
    print("\n📝 임시보관함 조회 중...")
    drafts_response = requests.get(
        f"{BASE_URL}{API_PREFIX}/mail/drafts?page=1&limit=10",
        headers=headers
    )
    
    if drafts_response.status_code == 200:
        drafts_result = drafts_response.json()
        draft_mails = drafts_result.get('mails', [])
        print(f"✅ 임시보관함 조회 성공! 총 {len(draft_mails)}개 메일")
        
        for mail in draft_mails:
            print(f"   - {mail.get('subject', 'N/A')} (UUID: {mail.get('mail_uuid', 'N/A')})")
    else:
        print(f"❌ 임시보관함 조회 실패: {drafts_response.text}")
    
    # 4. 발송함 조회
    print("\n📤 발송함 조회 중...")
    sent_response = requests.get(
        f"{BASE_URL}{API_PREFIX}/mail/sent?page=1&limit=10",
        headers=headers
    )
    
    if sent_response.status_code == 200:
        sent_result = sent_response.json()
        sent_mails = sent_result.get('mails', [])
        print(f"✅ 발송함 조회 성공! 총 {len(sent_mails)}개 메일")
        
        for mail in sent_mails:
            print(f"   - {mail.get('subject', 'N/A')} (UUID: {mail.get('mail_uuid', 'N/A')})")
    else:
        print(f"❌ 발송함 조회 실패: {sent_response.text}")
    
    # 5. 휴지통 조회 (현재 상태)
    print("\n🗑️ 휴지통 조회 (현재 상태) 중...")
    trash_response = requests.get(
        f"{BASE_URL}{API_PREFIX}/mail/trash?page=1&limit=10",
        headers=headers
    )
    
    if trash_response.status_code == 200:
        trash_result = trash_response.json()
        trash_mails = trash_result.get('mails', [])
        print(f"✅ 휴지통 조회 성공! 총 {len(trash_mails)}개 메일")
        
        if trash_mails:
            for mail in trash_mails:
                print(f"   - {mail.get('subject', 'N/A')} (상태: {mail.get('status', 'N/A')})")
        else:
            print("📭 휴지통이 비어있습니다.")
    else:
        print(f"❌ 휴지통 조회 실패: {trash_response.text}")
    
    # 6. 메일 상태별 필터링 테스트
    print("\n🔍 메일 상태별 필터링 테스트...")
    
    status_filters = ["inbox", "sent", "draft", "trash", "failed"]
    
    for status in status_filters:
        print(f"\n📋 상태 필터: {status}")
        
        # 휴지통에서 상태별 필터링
        filtered_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/mail/trash?page=1&limit=5&status={status}",
            headers=headers
        )
        
        if filtered_response.status_code == 200:
            filtered_result = filtered_response.json()
            total = filtered_result.get('pagination', {}).get('total', 0)
            mails = filtered_result.get('mails', [])
            print(f"   ✅ {status} 상태 메일 수: {total}")
            
            if mails:
                for mail in mails[:2]:  # 최대 2개만 표시
                    print(f"      - {mail.get('subject', 'N/A')} (상태: {mail.get('status', 'N/A')})")
        else:
            print(f"   ❌ {status} 필터링 실패: {filtered_response.status_code}")
            if filtered_response.status_code == 422:
                error_detail = filtered_response.json()
                print(f"      오류 상세: {error_detail.get('message', 'N/A')}")
    
    # 7. 검색 키워드 테스트
    print("\n🔍 검색 키워드 테스트...")
    
    search_keywords = ["휴지통", "테스트", "임시보관함"]
    
    for keyword in search_keywords:
        print(f"\n🔎 검색 키워드: '{keyword}'")
        
        search_response = requests.get(
            f"{BASE_URL}{API_PREFIX}/mail/trash?page=1&limit=5&search={keyword}",
            headers=headers
        )
        
        if search_response.status_code == 200:
            search_result = search_response.json()
            total = search_result.get('pagination', {}).get('total', 0)
            mails = search_result.get('mails', [])
            print(f"   ✅ '{keyword}' 검색 결과: {total}개")
            
            if mails:
                for mail in mails[:2]:  # 최대 2개만 표시
                    print(f"      - {mail.get('subject', 'N/A')}")
        else:
            print(f"   ❌ '{keyword}' 검색 실패: {search_response.status_code}")
    
    # 8. 메일 폴더 구조 확인
    print("\n📁 메일 폴더 구조 확인...")
    folders_response = requests.get(
        f"{BASE_URL}{API_PREFIX}/mail/folders",
        headers=headers
    )
    
    if folders_response.status_code == 200:
        folders_result = folders_response.json()
        folders = folders_result.get('data', {}).get('folders', [])
        print(f"✅ 폴더 조회 성공! 총 {len(folders)}개 폴더")
        
        for folder in folders:
            folder_type = folder.get('folder_type', 'N/A')
            folder_name = folder.get('name', 'N/A')
            mail_count = folder.get('mail_count', 0)
            print(f"   - {folder_name} ({folder_type}): {mail_count}개 메일")
    else:
        print(f"❌ 폴더 조회 실패: {folders_response.text}")
    
    print("\n" + "=" * 60)
    print("🏁 휴지통 API 테스트 완료!")
    print(f"⏰ 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 생성된 메일 정보 요약
    if created_mails:
        print(f"\n📋 생성된 테스트 메일 요약:")
        for mail in created_mails:
            print(f"   - {mail['subject']} (UUID: {mail['uuid']}, 임시보관: {mail['is_draft']})")

if __name__ == "__main__":
    test_trash_with_data()