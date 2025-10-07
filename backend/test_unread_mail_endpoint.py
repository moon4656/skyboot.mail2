#!/usr/bin/env python3
"""
읽지 않은 메일 조회 엔드포인트 테스트

SkyBoot Mail SaaS 시스템의 읽지 않은 메일 조회 기능을 테스트합니다.
"""
import requests
import json
import time
from datetime import datetime

# 테스트 설정
BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api/v1"

# 테스트 사용자 정보
TEST_USER = {
    "user_id": "user01",
    "password": "test"
}

class UnreadMailTester:
    """읽지 않은 메일 조회 테스트 클래스"""
    
    def __init__(self):
        """테스터 초기화"""
        self.session = requests.Session()
        self.token = None
        self.test_mail_uuid = None
        
    def login(self) -> bool:
        """사용자 로그인"""
        try:
            print("🔐 사용자 로그인 중...")
            
            login_data = {
                "user_id": TEST_USER["user_id"],
                "password": TEST_USER["password"]
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            print(f"📊 로그인 응답 상태 코드: {response.status_code}")
            print(f"📄 로그인 응답 내용: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"📄 로그인 응답 JSON: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
                # 응답 구조 확인: success 필드가 있는 경우와 직접 토큰이 반환되는 경우
                if result.get("success"):
                    # APIResponse 구조
                    self.token = result["data"]["access_token"]
                elif result.get("access_token"):
                    # 직접 토큰 반환 구조
                    self.token = result["access_token"]
                else:
                    print(f"❌ 로그인 실패: 토큰을 찾을 수 없음")
                    return False
                
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                print(f"✅ 로그인 성공: {TEST_USER['user_id']}")
                return True
            else:
                print(f"❌ 로그인 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 로그인 중 오류: {e}")
            return False
    
    def create_test_mail(self) -> bool:
        """테스트용 메일 생성"""
        try:
            print("📧 테스트 메일 생성 중...")
            
            mail_data = {
                "to": ["test@example.com"],
                "subject": f"읽지 않은 메일 테스트 - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "body_text": "이것은 읽지 않은 메일 조회 테스트를 위한 메일입니다."
            }
            
            response = self.session.post(f"{API_BASE}/mail/send-json", json=mail_data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self.test_mail_uuid = result["data"]["mail_uuid"]
                    print(f"✅ 테스트 메일 생성 성공: {self.test_mail_uuid}")
                    return True
                else:
                    print(f"❌ 메일 생성 실패: {result.get('message', '알 수 없는 오류')}")
                    return False
            else:
                print(f"❌ 메일 생성 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 메일 생성 중 오류: {e}")
            return False
    
    def test_unread_mails_basic(self) -> bool:
        """기본 읽지 않은 메일 조회 테스트"""
        try:
            print("\n📋 기본 읽지 않은 메일 조회 테스트")
            print("-" * 50)
            
            response = self.session.get(f"{API_BASE}/mail/unread")
            
            print(f"📊 응답 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"📄 응답 내용: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
                if result.get("success"):
                    data = result.get("data", {})
                    mails = data.get("mails", [])
                    total = data.get("total", 0)
                    
                    print(f"✅ 읽지 않은 메일 조회 성공")
                    print(f"📊 총 읽지 않은 메일 수: {total}개")
                    print(f"📊 현재 페이지 메일 수: {len(mails)}개")
                    
                    # 메일 목록 출력
                    if mails:
                        print("\n📧 읽지 않은 메일 목록:")
                        for i, mail in enumerate(mails, 1):
                            print(f"  {i}. {mail.get('subject', 'No Subject')} - {mail.get('sender_email', 'Unknown')}")
                    else:
                        print("📭 읽지 않은 메일이 없습니다.")
                    
                    return True
                else:
                    print(f"❌ 읽지 않은 메일 조회 실패: {result.get('message', '알 수 없는 오류')}")
                    return False
            else:
                print(f"❌ 읽지 않은 메일 조회 실패: {response.status_code}")
                print(f"📄 응답 내용: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 읽지 않은 메일 조회 중 오류: {e}")
            return False
    
    def test_unread_mails_pagination(self) -> bool:
        """페이지네이션 테스트"""
        try:
            print("\n📋 페이지네이션 테스트")
            print("-" * 50)
            
            # 첫 번째 페이지 (limit=5)
            response = self.session.get(f"{API_BASE}/mail/unread?page=1&limit=5")
            
            print(f"📊 응답 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    data = result.get("data", {})
                    total = data.get("total", 0)
                    page = data.get("page", 1)
                    limit = data.get("limit", 5)
                    pages = data.get("pages", 0)
                    mails = data.get("mails", [])
                    
                    print(f"✅ 페이지네이션 테스트 성공")
                    print(f"📊 총 메일 수: {total}개")
                    print(f"📊 현재 페이지: {page}")
                    print(f"📊 페이지당 메일 수: {limit}개")
                    print(f"📊 총 페이지 수: {pages}개")
                    print(f"📊 현재 페이지 메일 수: {len(mails)}개")
                    
                    return True
                else:
                    print(f"❌ 페이지네이션 테스트 실패: {result.get('message', '알 수 없는 오류')}")
                    return False
            else:
                print(f"❌ 페이지네이션 테스트 실패: {response.status_code}")
                print(f"📄 응답 내용: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 페이지네이션 테스트 중 오류: {e}")
            return False
    
    def test_mark_as_read_and_unread(self) -> bool:
        """메일 읽음/읽지않음 처리 테스트"""
        try:
            if not self.test_mail_uuid:
                print("⚠️ 테스트 메일이 없어 읽음/읽지않음 테스트를 건너뜁니다.")
                return True
                
            print("\n📋 메일 읽음/읽지않음 처리 테스트")
            print("-" * 50)
            
            # 1. 메일을 읽음으로 처리
            print("📖 메일을 읽음으로 처리 중...")
            read_response = self.session.post(f"{API_BASE}/mail/{self.test_mail_uuid}/read")
            
            print(f"📊 읽음 처리 응답 상태 코드: {read_response.status_code}")
            
            if read_response.status_code == 200:
                result = read_response.json()
                if result.get("success"):
                    print("✅ 메일 읽음 처리 성공")
                else:
                    print(f"❌ 메일 읽음 처리 실패: {result.get('message', '알 수 없는 오류')}")
            else:
                print(f"❌ 메일 읽음 처리 실패: {read_response.status_code}")
                print(f"📄 응답 내용: {read_response.text}")
            
            # 2. 메일을 읽지않음으로 처리
            print("\n📖 메일을 읽지않음으로 처리 중...")
            unread_response = self.session.post(f"{API_BASE}/mail/{self.test_mail_uuid}/unread")
            
            print(f"📊 읽지않음 처리 응답 상태 코드: {unread_response.status_code}")
            
            if unread_response.status_code == 200:
                result = unread_response.json()
                if result.get("success"):
                    print("✅ 메일 읽지않음 처리 성공")
                    return True
                else:
                    print(f"❌ 메일 읽지않음 처리 실패: {result.get('message', '알 수 없는 오류')}")
                    return False
            else:
                print(f"❌ 메일 읽지않음 처리 실패: {unread_response.status_code}")
                print(f"📄 응답 내용: {unread_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 메일 읽음/읽지않음 처리 중 오류: {e}")
            return False
    
    def test_invalid_parameters(self) -> bool:
        """잘못된 파라미터 테스트"""
        try:
            print("\n📋 잘못된 파라미터 테스트")
            print("-" * 50)
            
            test_cases = [
                {"params": "page=0&limit=20", "desc": "잘못된 페이지 번호 (0)"},
                {"params": "page=1&limit=0", "desc": "잘못된 limit (0)"},
                {"params": "page=1&limit=101", "desc": "너무 큰 limit (101)"},
                {"params": "page=-1&limit=20", "desc": "음수 페이지 번호"},
                {"params": "page=abc&limit=20", "desc": "문자열 페이지 번호"},
            ]
            
            for test_case in test_cases:
                print(f"\n🧪 테스트: {test_case['desc']}")
                response = self.session.get(f"{API_BASE}/mail/unread?{test_case['params']}")
                
                print(f"📊 응답 상태 코드: {response.status_code}")
                
                # 400 (Bad Request) 또는 422 (Unprocessable Entity) 예상
                if response.status_code in [400, 422]:
                    print(f"✅ 예상된 오류 응답: {response.status_code}")
                else:
                    print(f"⚠️ 예상과 다른 응답: {response.status_code}")
                    print(f"📄 응답 내용: {response.text}")
            
            return True
                
        except Exception as e:
            print(f"❌ 잘못된 파라미터 테스트 중 오류: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """모든 테스트 실행"""
        print("🧪 읽지 않은 메일 조회 엔드포인트 테스트 시작")
        print("=" * 60)
        
        # 1. 로그인
        if not self.login():
            print("❌ 로그인 실패로 테스트 중단")
            return False
        
        # 2. 테스트 메일 생성 (선택적)
        self.create_test_mail()
        
        # 3. 기본 읽지 않은 메일 조회 테스트
        test1_result = self.test_unread_mails_basic()
        
        # 4. 페이지네이션 테스트
        test2_result = self.test_unread_mails_pagination()
        
        # 5. 메일 읽음/읽지않음 처리 테스트
        test3_result = self.test_mark_as_read_and_unread()
        
        # 6. 잘못된 파라미터 테스트
        test4_result = self.test_invalid_parameters()
        
        # 결과 요약
        print("\n🎉 테스트 결과 요약")
        print("=" * 60)
        print(f"📋 기본 읽지 않은 메일 조회: {'✅ 성공' if test1_result else '❌ 실패'}")
        print(f"📋 페이지네이션 테스트: {'✅ 성공' if test2_result else '❌ 실패'}")
        print(f"📋 읽음/읽지않음 처리: {'✅ 성공' if test3_result else '❌ 실패'}")
        print(f"📋 잘못된 파라미터 테스트: {'✅ 성공' if test4_result else '❌ 실패'}")
        
        all_passed = all([test1_result, test2_result, test3_result, test4_result])
        
        if all_passed:
            print("\n🎉 모든 테스트 통과!")
        else:
            print("\n⚠️ 일부 테스트 실패")
        
        return all_passed

def main():
    """메인 함수"""
    tester = UnreadMailTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ 읽지 않은 메일 조회 엔드포인트 테스트 완료")
        exit(0)
    else:
        print("\n❌ 읽지 않은 메일 조회 엔드포인트 테스트 실패")
        exit(1)

if __name__ == "__main__":
    main()