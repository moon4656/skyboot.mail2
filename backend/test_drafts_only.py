import requests

# 로그인
login_data = {'user_id': 'user01', 'password': 'test'}
login_response = requests.post('http://localhost:8000/api/v1/auth/login', json=login_data)
print('로그인 응답 코드:', login_response.status_code)

if login_response.status_code == 200:
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # 임시보관함 조회
    print('임시보관함 조회 테스트...')
    drafts_response = requests.get('http://localhost:8000/api/v1/mail/drafts', headers=headers)
    print(f'응답 코드: {drafts_response.status_code}')
    if drafts_response.status_code != 200:
        print(f'오류: {drafts_response.text}')
    else:
        print('성공!')
        data = drafts_response.json()
        print(f'메일 수: {len(data.get("mails", []))}')
        print(f'전체 데이터: {data}')
else:
    print(f'로그인 실패: {login_response.text}')