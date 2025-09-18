import requests
import json

BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/auth/login"
STATS_URL = f"{BASE_URL}/mail/stats"

def test_stats_endpoint():
    """메일 통계 엔드포인트 테스트"""
    
    # 1. 로그인
    print("1. 로그인 중...")
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    login_response = requests.post(LOGIN_URL, json=login_data)
    
    if login_response.status_code != 200:
        print(f"로그인 실패: {login_response.status_code} - {login_response.text}")
        return
    
    token_data = login_response.json()
    access_token = token_data.get("access_token")
    
    if not access_token:
        print("토큰을 가져올 수 없습니다.")
        return
    
    print("로그인 성공!")
    
    # 2. 인증 헤더 설정
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 3. 통계 조회 테스트
    print("\n2. 메일 통계 조회 테스트...")
    
    try:
        response = requests.get(STATS_URL, headers=headers)
        
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("응답 데이터:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # 응답 구조 검증
            if "stats" in data:
                stats = data["stats"]
                print("\n통계 정보:")
                print(f"- 총 발송 메일: {stats.get('total_sent', 0)}")
                print(f"- 총 수신 메일: {stats.get('total_received', 0)}")
                print(f"- 총 임시보관 메일: {stats.get('total_drafts', 0)}")
                print(f"- 읽지 않은 메일: {stats.get('unread_count', 0)}")
                print(f"- 오늘 발송 메일: {stats.get('today_sent', 0)}")
                print(f"- 오늘 수신 메일: {stats.get('today_received', 0)}")
                print("\n✅ 통계 엔드포인트 테스트 성공!")
            else:
                print("❌ 응답에 'stats' 필드가 없습니다.")
        else:
            print(f"❌ 통계 조회 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    test_stats_endpoint()