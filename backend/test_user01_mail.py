import requests
import json

# API 서버 URL
BASE_URL = 'http://localhost:8000/api/v1'

def login_user01():
    """user01로 로그인하고 토큰 반환"""
    login_data = {
        'user_id': 'user01',
        'password': 'test'
    }
    
    response = requests.post(f'{BASE_URL}/auth/login', json=login_data)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"로그인 실패: {response.text}")

try:
    print('=== user01 메일 기능 테스트 ===')
    
    # 1. 로그인
    token = login_user01()
    headers = {'Authorization': f'Bearer {token}'}
    print('✅ 로그인 성공')
    
    # 2. 받은편지함 조회
    print('\n--- 받은편지함 조회 ---')
    inbox_response = requests.get(f'{BASE_URL}/mail/inbox', headers=headers)
    print(f'받은편지함 응답: {inbox_response.status_code}')
    if inbox_response.status_code == 200:
        inbox_data = inbox_response.json()
        print(f'받은편지함 메일 수: {len(inbox_data.get("mails", []))}')
        print(f'총 메일 수: {inbox_data.get("total", 0)}')
    else:
        print(f'받은편지함 조회 실패: {inbox_response.text}')
    
    # 3. 임시보관함 조회
    print('\n--- 임시보관함 조회 ---')
    drafts_response = requests.get(f'{BASE_URL}/mail/drafts', headers=headers)
    print(f'임시보관함 응답: {drafts_response.status_code}')
    if drafts_response.status_code == 200:
        drafts_data = drafts_response.json()
        print(f'임시보관함 메일 수: {len(drafts_data.get("mails", []))}')
        print(f'총 메일 수: {drafts_data.get("total", 0)}')
    else:
        print(f'임시보관함 조회 실패: {drafts_response.text}')
    
    # 4. 보낸편지함 조회
    print('\n--- 보낸편지함 조회 ---')
    sent_response = requests.get(f'{BASE_URL}/mail/sent', headers=headers)
    print(f'보낸편지함 응답: {sent_response.status_code}')
    if sent_response.status_code == 200:
        sent_data = sent_response.json()
        print(f'보낸편지함 메일 수: {len(sent_data.get("mails", []))}')
        print(f'총 메일 수: {sent_data.get("total", 0)}')
    else:
        print(f'보낸편지함 조회 실패: {sent_response.text}')
    
    # 5. 메일 폴더 목록 조회
    print('\n--- 메일 폴더 목록 조회 ---')
    folders_response = requests.get(f'{BASE_URL}/mail/folders', headers=headers)
    print(f'폴더 목록 응답: {folders_response.status_code}')
    if folders_response.status_code == 200:
        folders_data = folders_response.json()
        print(f'폴더 수: {len(folders_data.get("folders", []))}')
        for folder in folders_data.get("folders", []):
            print(f'- {folder.get("name", "이름없음")} ({folder.get("folder_type", "타입없음")})')
    else:
        print(f'폴더 목록 조회 실패: {folders_response.text}')
    
    # 6. 테스트 메일 발송 (Form 데이터 사용)
    print('\n--- 테스트 메일 발송 ---')
    mail_data = {
        'to_emails': 'test@example.com',
        'subject': 'user01 테스트 메일',
        'content': 'user01 계정에서 발송하는 테스트 메일입니다.',
        'priority': 'normal',
        'is_draft': 'false'
    }
    
    send_response = requests.post(f'{BASE_URL}/mail/send', data=mail_data, headers=headers)
    print(f'메일 발송 응답: {send_response.status_code}')
    if send_response.status_code == 200:
        send_result = send_response.json()
        print(f'✅ 메일 발송 성공: {send_result.get("message", "성공")}')
        if 'mail_id' in send_result:
            print(f'메일 ID: {send_result["mail_id"]}')
    else:
        print(f'❌ 메일 발송 실패: {send_response.text}')
    
    # 7. 임시보관함에 메일 저장 테스트
    print('\n--- 임시보관함 저장 테스트 ---')
    draft_data = {
        'to_emails': 'draft@example.com',
        'subject': 'user01 임시보관 메일',
        'content': 'user01 계정에서 임시보관하는 메일입니다.',
        'priority': 'normal',
        'is_draft': 'true'
    }
    
    draft_response = requests.post(f'{BASE_URL}/mail/send', data=draft_data, headers=headers)
    print(f'임시보관 응답: {draft_response.status_code}')
    if draft_response.status_code == 200:
        draft_result = draft_response.json()
        print(f'✅ 임시보관 성공: {draft_result.get("message", "성공")}')
        if 'mail_id' in draft_result:
            print(f'임시보관 메일 ID: {draft_result["mail_id"]}')
    else:
        print(f'❌ 임시보관 실패: {draft_response.text}')
    
    print('\n=== user01 메일 기능 테스트 완료 ===')

except Exception as e:
    print(f'❌ 오류 발생: {e}')
    import traceback
    traceback.print_exc()