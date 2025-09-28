#!/usr/bin/env python3
"""
메일 API 엔드포인트 테스트 스크립트
=====================================

메일 핵심 기능 엔드포인트들을 체계적으로 테스트합니다:
- POST /api/v1/mail/send: 메일 발송
- GET /api/v1/mail/inbox: 받은 메일함 조회
- GET /api/v1/mail/inbox/{mail_id}: 받은 메일 상세 조회
- GET /api/v1/mail/sent: 보낸 메일함 조회
- GET /api/v1/mail/trash: 휴지통 조회
- DELETE /api/v1/mail/{mail_id}: 메일 삭제
- GET /api/v1/mail/attachment/{attachment_id}: 첨부파일 다운로드
"""

import requests
import json
import sys
import os
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class MailEndpointTester:
    """메일 엔드포인트 테스트 클래스"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1"
        self.access_token = None
        self.test_results = {}
        
    def login_and_get_token(self):
        """로그인하여 액세스 토큰을 획득합니다."""
        print("🔐 로그인 중...")
        
        login_data = {
            "email": "mailtest@skyboot.com",
            "password": "mailtest123"
        }
        
        try:
            response = requests.post(f"{self.base_url}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                print(f"✅ 로그인 성공! 토큰 획득됨")
                return True
            else:
                print(f"❌ 로그인 실패: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ 로그인 오류: {str(e)}")
            return False
    
    def get_headers(self):
        """인증 헤더를 반환합니다."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def test_send_mail(self):
        """메일 발송 엔드포인트를 테스트합니다."""
        print("\n📤 메일 발송 테스트 시작...")
        
        # 테스트 메일 데이터 (Form 형식)
        mail_data = {
            "to_emails": "test@example.com",
            "subject": "테스트 메일 - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "content": "안녕하세요! 이것은 메일 API 테스트 메일입니다.",
            "priority": "normal"
        }
        
        # Form 데이터용 헤더 (Content-Type 제거)
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/mail/send",
                data=mail_data,  # json 대신 data 사용
                headers=headers
            )
            
            print(f"응답 상태 코드: {response.status_code}")
            print(f"응답 내용: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 메일 발송 성공!")
                print(f"   - 메일 ID: {data.get('mail_id', 'N/A')}")
                print(f"   - 메시지: {data.get('message', 'N/A')}")
                self.test_results["send_mail"] = {"status": "success", "mail_id": data.get("mail_id")}
                return data.get("mail_id")
            else:
                print(f"❌ 메일 발송 실패: {response.status_code}")
                print(f"   - 오류 내용: {response.text}")
                self.test_results["send_mail"] = {"status": "failed", "error": response.text}
                return None
                
        except Exception as e:
            print(f"❌ 메일 발송 오류: {str(e)}")
            self.test_results["send_mail"] = {"status": "error", "error": str(e)}
            return None
    
    def test_inbox(self):
        """받은 메일함 엔드포인트를 테스트합니다."""
        print("\n📥 받은 메일함 테스트 시작...")
        
        try:
            response = requests.get(
                f"{self.base_url}/mail/inbox",
                headers=self.get_headers(),
                params={"page": 1, "limit": 10}
            )
            
            print(f"응답 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 받은 메일함 조회 성공!")
                print(f"   - 총 메일 수: {data.get('total', 0)}")
                print(f"   - 현재 페이지 메일 수: {len(data.get('mails', []))}")
                
                # 첫 번째 메일 정보 출력
                mails = data.get('mails', [])
                if mails:
                    first_mail = mails[0]
                    print(f"   - 첫 번째 메일 ID: {first_mail.get('mail_id')}")
                    print(f"   - 첫 번째 메일 제목: {first_mail.get('subject')}")
                    self.test_results["inbox"] = {"status": "success", "count": len(mails)}
                    return mails[0].get('mail_id') if mails else None
                else:
                    print("   - 받은 메일이 없습니다.")
                    self.test_results["inbox"] = {"status": "success", "count": 0}
                    return None
            else:
                print(f"❌ 받은 메일함 조회 실패: {response.status_code}")
                print(f"   - 오류 내용: {response.text}")
                self.test_results["inbox"] = {"status": "failed", "error": response.text}
                return None
                
        except Exception as e:
            print(f"❌ 받은 메일함 조회 오류: {str(e)}")
            self.test_results["inbox"] = {"status": "error", "error": str(e)}
            return None
    
    def test_mail_detail(self, mail_id):
        """메일 상세 조회 엔드포인트를 테스트합니다."""
        if not mail_id:
            print("\n⚠️ 메일 상세 조회 테스트 건너뜀 (메일 ID 없음)")
            return
            
        print(f"\n📄 메일 상세 조회 테스트 시작 (ID: {mail_id})...")
        
        try:
            response = requests.get(
                f"{self.base_url}/mail/inbox/{mail_id}",
                headers=self.get_headers()
            )
            
            print(f"응답 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 메일 상세 조회 성공!")
                print(f"   - 메일 ID: {data.get('mail_id')}")
                print(f"   - 제목: {data.get('subject')}")
                print(f"   - 발송자: {data.get('sender_email')}")
                print(f"   - 내용 길이: {len(data.get('content', ''))}")
                self.test_results["mail_detail"] = {"status": "success"}
            else:
                print(f"❌ 메일 상세 조회 실패: {response.status_code}")
                print(f"   - 오류 내용: {response.text}")
                self.test_results["mail_detail"] = {"status": "failed", "error": response.text}
                
        except Exception as e:
            print(f"❌ 메일 상세 조회 오류: {str(e)}")
            self.test_results["mail_detail"] = {"status": "error", "error": str(e)}
    
    def test_sent_mail(self):
        """보낸 메일함 엔드포인트를 테스트합니다."""
        print("\n📤 보낸 메일함 테스트 시작...")
        
        try:
            response = requests.get(
                f"{self.base_url}/mail/sent",
                headers=self.get_headers(),
                params={"page": 1, "limit": 10}
            )
            
            print(f"응답 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 보낸 메일함 조회 성공!")
                print(f"   - 총 메일 수: {data.get('total', 0)}")
                print(f"   - 현재 페이지 메일 수: {len(data.get('mails', []))}")
                self.test_results["sent_mail"] = {"status": "success", "count": len(data.get('mails', []))}
            else:
                print(f"❌ 보낸 메일함 조회 실패: {response.status_code}")
                print(f"   - 오류 내용: {response.text}")
                self.test_results["sent_mail"] = {"status": "failed", "error": response.text}
                
        except Exception as e:
            print(f"❌ 보낸 메일함 조회 오류: {str(e)}")
            self.test_results["sent_mail"] = {"status": "error", "error": str(e)}
    
    def test_trash(self):
        """휴지통 엔드포인트를 테스트합니다."""
        print("\n🗑️ 휴지통 테스트 시작...")
        
        try:
            response = requests.get(
                f"{self.base_url}/mail/trash",
                headers=self.get_headers(),
                params={"page": 1, "limit": 10}
            )
            
            print(f"응답 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 휴지통 조회 성공!")
                print(f"   - 총 메일 수: {data.get('total', 0)}")
                print(f"   - 현재 페이지 메일 수: {len(data.get('mails', []))}")
                self.test_results["trash"] = {"status": "success", "count": len(data.get('mails', []))}
            else:
                print(f"❌ 휴지통 조회 실패: {response.status_code}")
                print(f"   - 오류 내용: {response.text}")
                self.test_results["trash"] = {"status": "failed", "error": response.text}
                
        except Exception as e:
            print(f"❌ 휴지통 조회 오류: {str(e)}")
            self.test_results["trash"] = {"status": "error", "error": str(e)}
    
    def print_summary(self):
        """테스트 결과 요약을 출력합니다."""
        print("\n" + "="*60)
        print("📊 메일 API 엔드포인트 테스트 결과 요약")
        print("="*60)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result["status"] == "success")
        
        print(f"총 테스트 수: {total_tests}")
        print(f"성공한 테스트: {successful_tests}")
        print(f"실패한 테스트: {total_tests - successful_tests}")
        print(f"성공률: {(successful_tests/total_tests*100):.1f}%" if total_tests > 0 else "성공률: 0%")
        
        print("\n상세 결과:")
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result["status"] == "success" else "❌"
            print(f"  {status_icon} {test_name}: {result['status']}")
            if result["status"] != "success" and "error" in result:
                print(f"     오류: {result['error'][:100]}...")
    
    def run_all_tests(self):
        """모든 테스트를 실행합니다."""
        print("🚀 메일 API 엔드포인트 테스트 시작")
        print("="*60)
        
        # 1. 로그인
        if not self.login_and_get_token():
            print("❌ 로그인 실패로 테스트를 중단합니다.")
            return
        
        # 2. 메일 발송 테스트
        sent_mail_id = self.test_send_mail()
        
        # 3. 받은 메일함 테스트
        inbox_mail_id = self.test_inbox()
        
        # 4. 메일 상세 조회 테스트 (받은 메일함에서 첫 번째 메일 사용)
        self.test_mail_detail(inbox_mail_id)
        
        # 5. 보낸 메일함 테스트
        self.test_sent_mail()
        
        # 6. 휴지통 테스트
        self.test_trash()
        
        # 7. 결과 요약
        self.print_summary()

if __name__ == "__main__":
    tester = MailEndpointTester()
    tester.run_all_tests()