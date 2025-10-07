#!/usr/bin/env python3
"""
휴지통 종합 테스트 스크립트
user01과 test 계정으로 휴지통 내역 생성 및 조회 테스트

테스트 시나리오:
1. 두 계정으로 로그인
2. 각 계정에서 다양한 상태의 메일 생성 (임시보관함, 발송함)
3. 생성된 메일을 휴지통으로 이동
4. 휴지통 조회 및 필터링 테스트
5. 결과 검증
"""

import requests
import json
from datetime import datetime
import time
import uuid

# 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# 테스트 계정 정보
TEST_ACCOUNTS = [
    {
        "username": "user01",
        "password": "test",
        "email": "user01@example.com"
    }
]

class TrashTestManager:
    """휴지통 테스트 관리 클래스"""
    
    def __init__(self):
        self.session_data = {}
        self.created_mails = {}
        
    def log_test(self, message, level="INFO"):
        """테스트 로그 출력"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")
        
    def login_user(self, username, password):
        """사용자 로그인"""
        try:
            self.log_test(f"🔐 {username} 계정 로그인 시도...")
            
            login_data = {
                "user_id": username,
                "password": password
            }
            
            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                token = result.get("access_token")
                
                if token:
                    self.session_data[username] = {
                        "token": token,
                        "headers": {"Authorization": f"Bearer {token}"}
                    }
                    self.log_test(f"✅ {username} 로그인 성공!")
                    return True
                else:
                    self.log_test(f"❌ {username} 토큰 없음", "ERROR")
                    return False
            else:
                self.log_test(f"❌ {username} 로그인 실패: {response.status_code}", "ERROR")
                self.log_test(f"응답: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log_test(f"❌ {username} 로그인 예외: {str(e)}", "ERROR")
            return False
    
    def create_test_mails(self, username):
        """테스트용 메일 생성"""
        try:
            self.log_test(f"📧 {username} 계정 테스트 메일 생성 중...")
            
            if username not in self.session_data:
                self.log_test(f"❌ {username} 세션 데이터 없음", "ERROR")
                return False
                
            headers = self.session_data[username]["headers"]
            created_mails = []
            
            # 1. 임시보관함 메일 생성 (3개)
            for i in range(1, 4):
                draft_data = {
                    "to": [f"recipient{i}@example.com"],
                    "subject": f"[{username}] 임시보관함 테스트 메일 {i}",
                    "body_text": f"이것은 {username} 계정의 임시보관함 테스트 메일 {i}번입니다.",
                    "is_draft": True
                }
                
                response = requests.post(
                    f"{BASE_URL}{API_PREFIX}/mail/send-json",
                    json=draft_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    mail_uuid = result.get("mail_uuid")
                    if mail_uuid:
                        created_mails.append({
                            "uuid": mail_uuid,
                            "type": "draft",
                            "subject": draft_data["subject"]
                        })
                        self.log_test(f"   ✅ 임시보관함 메일 {i} 생성: {mail_uuid}")
                    else:
                        self.log_test(f"   ❌ 임시보관함 메일 {i} UUID 없음", "WARNING")
                else:
                    self.log_test(f"   ❌ 임시보관함 메일 {i} 생성 실패: {response.status_code}", "ERROR")
                    self.log_test(f"   응답: {response.text}", "ERROR")
                
                time.sleep(0.5)  # API 호출 간격
            
            # 2. 발송 메일 생성 (SMTP 서버 필요로 인해 주석 처리)
            # for i in range(1, 3):
            #     send_data = {
            #         "to": [f"sent{i}@example.com"],
            #         "subject": f"[{username}] 발송 테스트 메일 {i}",
            #         "body_text": f"이것은 {username} 계정의 발송 테스트 메일 {i}번입니다.",
            #         "is_draft": False
            #     }
            #     
            #     response = requests.post(
            #         f"{BASE_URL}{API_PREFIX}/mail/send-json",
            #         json=send_data,
            #         headers=headers
            #     )
            #     
            #     if response.status_code == 200:
            #         result = response.json()
            #         mail_uuid = result.get("mail_uuid")
            #         if mail_uuid:
            #             created_mails.append({
            #                 "uuid": mail_uuid,
            #                 "type": "sent",
            #                 "subject": send_data["subject"]
            #             })
            #             self.log_test(f"   ✅ 발송 메일 {i} 생성: {mail_uuid}")
            #         else:
            #             self.log_test(f"   ❌ 발송 메일 {i} UUID 없음", "WARNING")
            #     else:
            #         self.log_test(f"   ❌ 발송 메일 {i} 생성 실패: {response.status_code}", "ERROR")
            #         self.log_test(f"   응답: {response.text}", "ERROR")
            #     
            #     time.sleep(0.5)  # API 호출 간격
            
            self.created_mails[username] = created_mails
            self.log_test(f"✅ {username} 계정 메일 생성 완료: {len(created_mails)}개")
            return True
            
        except Exception as e:
            self.log_test(f"❌ {username} 메일 생성 예외: {str(e)}", "ERROR")
            return False
    
    def move_mails_to_trash(self, username):
        """생성된 메일을 휴지통으로 이동"""
        try:
            self.log_test(f"🗑️ {username} 계정 메일을 휴지통으로 이동 중...")
            
            if username not in self.created_mails or not self.created_mails[username]:
                self.log_test(f"❌ {username} 생성된 메일 없음", "ERROR")
                return False
                
            headers = self.session_data[username]["headers"]
            moved_count = 0
            
            # 생성된 메일 중 일부를 휴지통으로 이동 (첫 번째와 마지막 메일)
            mails_to_move = [
                self.created_mails[username][0],  # 첫 번째 메일
                self.created_mails[username][-1]  # 마지막 메일
            ]
            
            for mail in mails_to_move:
                mail_uuid = mail["uuid"]
                
                # 메일 삭제 API 호출 (휴지통으로 이동)
                delete_response = requests.delete(
                    f"{BASE_URL}{API_PREFIX}/mail/{mail_uuid}?permanent=false",
                    headers=headers
                )
                
                if delete_response.status_code == 200:
                    result = delete_response.json()
                    if result.get("success"):
                        moved_count += 1
                        self.log_test(f"   ✅ 메일 휴지통 이동: {mail['subject']}")
                    else:
                        self.log_test(f"   ❌ 메일 이동 실패: {result.get('message', 'Unknown error')}", "WARNING")
                else:
                    self.log_test(f"   ❌ 메일 삭제 API 실패: {delete_response.status_code}", "WARNING")
                    self.log_test(f"   응답: {delete_response.text}", "WARNING")
                
                time.sleep(0.5)  # API 호출 간격
            
            self.log_test(f"✅ {username} 계정 휴지통 이동 완료: {moved_count}개")
            return moved_count > 0
            
        except Exception as e:
            self.log_test(f"❌ {username} 휴지통 이동 예외: {str(e)}", "ERROR")
            return False
    
    def test_trash_query(self, username):
        """휴지통 조회 테스트"""
        try:
            self.log_test(f"🔍 {username} 계정 휴지통 조회 테스트...")
            
            headers = self.session_data[username]["headers"]
            
            # 1. 기본 휴지통 조회
            self.log_test(f"   📋 기본 휴지통 조회...")
            response = requests.get(
                f"{BASE_URL}{API_PREFIX}/mail/trash?page=1&limit=10",
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                total = result.get("pagination", {}).get("total", 0)
                mails = result.get("mails", [])
                
                self.log_test(f"   ✅ 휴지통 총 메일 수: {total}")
                
                if mails:
                    self.log_test(f"   📧 휴지통 메일 목록:")
                    for i, mail in enumerate(mails[:3], 1):
                        subject = mail.get("subject", "N/A")
                        status = mail.get("status", "N/A")
                        self.log_test(f"      {i}. {subject} (상태: {status})")
                else:
                    self.log_test(f"   📭 휴지통이 비어있습니다")
            else:
                self.log_test(f"   ❌ 휴지통 조회 실패: {response.status_code}", "ERROR")
                return False
            
            # 2. 상태별 필터링 테스트
            self.log_test(f"   🔍 상태별 필터링 테스트...")
            status_filters = ["draft", "sent", "trash", "failed"]
            
            for status in status_filters:
                filter_response = requests.get(
                    f"{BASE_URL}{API_PREFIX}/mail/trash?page=1&limit=5&status={status}",
                    headers=headers
                )
                
                if filter_response.status_code == 200:
                    filter_result = filter_response.json()
                    filter_total = filter_result.get("pagination", {}).get("total", 0)
                    self.log_test(f"      📊 {status} 상태: {filter_total}개")
                else:
                    self.log_test(f"      ❌ {status} 필터링 실패: {filter_response.status_code}", "WARNING")
            
            # 3. 검색 테스트
            self.log_test(f"   🔎 검색 테스트...")
            search_keywords = [username, "테스트", "임시보관함"]
            
            for keyword in search_keywords:
                search_response = requests.get(
                    f"{BASE_URL}{API_PREFIX}/mail/trash?page=1&limit=5&search={keyword}",
                    headers=headers
                )
                
                if search_response.status_code == 200:
                    search_result = search_response.json()
                    search_total = search_result.get("pagination", {}).get("total", 0)
                    self.log_test(f"      🔍 '{keyword}' 검색: {search_total}개")
                else:
                    self.log_test(f"      ❌ '{keyword}' 검색 실패: {search_response.status_code}", "WARNING")
            
            return True
            
        except Exception as e:
            self.log_test(f"❌ {username} 휴지통 조회 예외: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_test(self):
        """종합 테스트 실행"""
        self.log_test("🚀 휴지통 종합 테스트 시작!")
        self.log_test("=" * 60)
        
        success_count = 0
        total_accounts = len(TEST_ACCOUNTS)
        
        for account in TEST_ACCOUNTS:
            username = account["username"]
            password = account["password"]
            
            self.log_test(f"\n👤 {username} 계정 테스트 시작...")
            self.log_test("-" * 40)
            
            # 1. 로그인
            if not self.login_user(username, password):
                self.log_test(f"❌ {username} 계정 테스트 실패 (로그인)", "ERROR")
                continue
            
            # 2. 테스트 메일 생성
            if not self.create_test_mails(username):
                self.log_test(f"❌ {username} 계정 테스트 실패 (메일 생성)", "ERROR")
                continue
            
            # 3. 휴지통으로 이동
            if not self.move_mails_to_trash(username):
                self.log_test(f"⚠️ {username} 계정 휴지통 이동 실패", "WARNING")
                # 휴지통 이동이 실패해도 조회 테스트는 진행
            
            # 4. 휴지통 조회 테스트
            if self.test_trash_query(username):
                success_count += 1
                self.log_test(f"✅ {username} 계정 테스트 완료!")
            else:
                self.log_test(f"❌ {username} 계정 테스트 실패 (휴지통 조회)", "ERROR")
        
        # 결과 요약
        self.log_test("\n" + "=" * 60)
        self.log_test("🏁 휴지통 종합 테스트 완료!")
        self.log_test(f"📊 성공한 계정: {success_count}/{total_accounts}")
        
        if success_count == total_accounts:
            self.log_test("🎉 모든 계정 테스트 성공!")
        elif success_count > 0:
            self.log_test("⚠️ 일부 계정 테스트 성공")
        else:
            self.log_test("❌ 모든 계정 테스트 실패")
        
        # 생성된 메일 요약
        self.log_test(f"\n📋 생성된 메일 요약:")
        for username, mails in self.created_mails.items():
            self.log_test(f"   {username}: {len(mails)}개 메일")
            for mail in mails:
                self.log_test(f"      - {mail['subject']} ({mail['type']})")
        
        self.log_test(f"\n⏰ 테스트 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """메인 함수"""
    test_manager = TrashTestManager()
    test_manager.run_comprehensive_test()

if __name__ == "__main__":
    main()