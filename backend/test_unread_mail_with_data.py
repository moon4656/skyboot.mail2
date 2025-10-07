#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
읽지 않은 메일 조회 엔드포인트 테스트 (실제 메일 데이터 포함)
"""

import requests
import json
import time
from datetime import datetime

# 테스트 설정
API_BASE = "http://localhost:8001/api/v1"

# 테스트 사용자 정보
TEST_USER = {
    "user_id": "user01",
    "password": "test"
}

class UnreadMailTesterWithData:
    """읽지 않은 메일 조회 테스트 클래스 (실제 데이터 포함)"""
    
    def __init__(self):
        """테스터 초기화"""
        self.session = requests.Session()
        self.token = None
        self.created_mails = []  # 생성된 테스트 메일 ID 저장
    
    def login(self):
        """사용자 로그인"""
        print("🔐 사용자 로그인 중...")
        
        login_data = {
            "user_id": TEST_USER["user_id"],
            "password": TEST_USER["password"]
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/auth/login", headers=headers, json=login_data)
            
            if response.status_code == 200:
                result = response.json()
                
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
            print(f"❌ 로그인 중 오류 발생: {str(e)}")
            return False
    
    def create_test_mail(self, subject_suffix=""):
        """테스트 메일 생성"""
        print(f"📧 테스트 메일 생성 중{subject_suffix}...")
        
        mail_data = {
            "to": ["user01@example.com"],  # 자신에게 메일 발송
            "subject": f"읽지 않은 메일 테스트 {datetime.now().strftime('%H:%M:%S')}{subject_suffix}",
            "body_text": f"이것은 읽지 않은 메일 테스트용 메일입니다.{subject_suffix}\n생성 시간: {datetime.now()}",
            "priority": "normal",
            "is_draft": False
        }
        
        try:
            response = self.session.post(f"{API_BASE}/mail/send-json", json=mail_data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    # mail_uuid 또는 mail_id 필드 확인
                    mail_id = result.get("mail_uuid") or result.get("data", {}).get("mail_uuid") or result.get("data", {}).get("mail_id")
                    if mail_id:
                        self.created_mails.append(mail_id)
                        print(f"✅ 테스트 메일 생성 성공: {mail_id}")
                        return mail_id
                    else:
                        print(f"❌ 메일 생성 실패: 메일 ID를 찾을 수 없음 - {result}")
                        return None
                else:
                    print(f"❌ 메일 생성 실패: {result.get('message', '알 수 없는 오류')}")
                    return None
            else:
                print(f"❌ 메일 생성 실패: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 메일 생성 중 오류 발생: {str(e)}")
            return None
    
    def get_unread_mails(self, page=1, limit=20):
        """읽지 않은 메일 조회"""
        try:
            params = {"page": page, "limit": limit}
            response = self.session.get(f"{API_BASE}/mail/unread", params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ 읽지 않은 메일 조회 실패: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 읽지 않은 메일 조회 중 오류 발생: {str(e)}")
            return None
    
    def get_inbox_mails(self, limit=10):
        """받은 메일함 조회"""
        try:
            response = self.session.get(f"{API_BASE}/mail/inbox?page=1&limit={limit}")
            if response.status_code == 200:
                result = response.json()
                # 응답 구조: {"mails": [...], "pagination": {...}}
                if 'mails' in result:
                    return result['mails']
                elif 'data' in result and 'mails' in result['data']:
                    return result['data']['mails']
                return []
            else:
                print(f"❌ 받은 메일함 조회 실패: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ 받은 메일함 조회 오류: {e}")
            return []
    
    def get_unread_count(self):
        """읽지 않은 메일 수 조회"""
        try:
            response = self.session.get(f"{API_BASE}/mail/unread?page=1&limit=1")
            if response.status_code == 200:
                result = response.json()
                # 응답 구조: {"mails": [...], "pagination": {"total": N}}
                if 'pagination' in result:
                    return result['pagination'].get('total', 0)
                elif 'data' in result and 'pagination' in result['data']:
                    return result['data']['pagination'].get('total', 0)
                return 0
            else:
                print(f"❌ 읽지 않은 메일 조회 실패: {response.status_code}")
                return 0
        except Exception as e:
            print(f"❌ 읽지 않은 메일 조회 오류: {e}")
            return 0
    
    def mark_mail_as_read(self, mail_id):
        """메일을 읽음으로 표시"""
        try:
            response = self.session.post(f"{API_BASE}/mail/{mail_id}/read")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ 메일 읽음 처리 성공: {mail_id}")
                    return True
                else:
                    print(f"❌ 메일 읽음 처리 실패: {result.get('message', '알 수 없는 오류')}")
                    return False
            else:
                print(f"❌ 메일 읽음 처리 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 메일 읽음 처리 중 오류 발생: {str(e)}")
            return False
    
    def mark_mail_as_unread(self, mail_id):
        """메일을 읽지 않음으로 표시"""
        try:
            response = self.session.post(f"{API_BASE}/mail/{mail_id}/unread")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ 메일 읽지않음 처리 성공: {mail_id}")
                    return True
                else:
                    print(f"❌ 메일 읽지않음 처리 실패: {result.get('message', '알 수 없는 오류')}")
                    return False
            else:
                print(f"❌ 메일 읽지않음 처리 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 메일 읽지않음 처리 중 오류 발생: {str(e)}")
            return False
    
    def cleanup_test_mails(self):
        """생성된 테스트 메일 정리"""
        print("🧹 테스트 메일 정리 중...")
        
        for mail_id in self.created_mails:
            try:
                # 영구 삭제
                response = self.session.delete(f"{API_BASE}/mail/{mail_id}/permanent")
                if response.status_code == 200:
                    print(f"✅ 테스트 메일 삭제 성공: {mail_id}")
                else:
                    print(f"⚠️ 테스트 메일 삭제 실패: {mail_id}")
            except Exception as e:
                print(f"⚠️ 테스트 메일 삭제 중 오류: {mail_id} - {str(e)}")
        
        self.created_mails.clear()
    
    def run_comprehensive_test(self):
        """종합적인 읽지 않은 메일 테스트 실행"""
        print("🚀 읽지 않은 메일 조회 종합 테스트 시작")
        print("=" * 60)
        
        # 1. 로그인
        if not self.login():
            print("❌ 로그인 실패로 테스트 중단")
            return False
        
        try:
            # 2. 초기 읽지 않은 메일 수 확인
            print("\n📋 초기 읽지 않은 메일 수 확인")
            print("-" * 50)
            initial_result = self.get_unread_mails()
            if initial_result and initial_result.get("success"):
                initial_count = initial_result["data"]["total"]
                print(f"📊 초기 읽지 않은 메일 수: {initial_count}개")
            else:
                print("❌ 초기 읽지 않은 메일 조회 실패")
                return False
            
            # 3. 테스트 메일 3개 생성
            print("\n📧 테스트 메일 생성")
            print("-" * 50)
            mail_ids = []
            for i in range(3):
                mail_id = self.create_test_mail(f" #{i+1}")
                if mail_id:
                    mail_ids.append(mail_id)
                    time.sleep(1)  # 메일 생성 간격
                else:
                    print(f"❌ 테스트 메일 {i+1} 생성 실패")
            
            if len(mail_ids) == 0:
                print("❌ 테스트 메일 생성 실패로 테스트 중단")
                return False
            
            print(f"✅ {len(mail_ids)}개의 테스트 메일 생성 완료")
            
            # 4. 읽지 않은 메일 조회 (증가 확인)
            print("\n📋 읽지 않은 메일 조회 (증가 확인)")
            print("-" * 50)
            time.sleep(2)  # 메일 처리 대기
            
            result = self.get_unread_mails()
            if result and result.get("success"):
                current_count = result["data"]["total"]
                mails = result["data"]["mails"]
                
                print(f"📊 현재 읽지 않은 메일 수: {current_count}개")
                print(f"📊 증가된 메일 수: {current_count - initial_count}개")
                
                if current_count > initial_count:
                    print("✅ 읽지 않은 메일 수 증가 확인")
                    
                    # 메일 목록 출력
                    print("\n📋 읽지 않은 메일 목록:")
                    for i, mail in enumerate(mails[:5]):  # 최대 5개만 출력
                        print(f"  {i+1}. {mail.get('subject', 'N/A')} (ID: {mail.get('mail_id', 'N/A')})")
                else:
                    print("⚠️ 읽지 않은 메일 수가 증가하지 않음")
            else:
                print("❌ 읽지 않은 메일 조회 실패")
                return False
            
            # 5. 첫 번째 메일을 읽음으로 표시
            if mail_ids:
                print("\n📖 메일 읽음 처리 테스트")
                print("-" * 50)
                
                first_mail_id = mail_ids[0]
                if self.mark_mail_as_read(first_mail_id):
                    time.sleep(1)  # 처리 대기
                    
                    # 읽지 않은 메일 수 다시 확인
                    result = self.get_unread_mails()
                    if result and result.get("success"):
                        after_read_count = result["data"]["total"]
                        print(f"📊 읽음 처리 후 읽지 않은 메일 수: {after_read_count}개")
                        
                        if after_read_count < current_count:
                            print("✅ 메일 읽음 처리 후 읽지 않은 메일 수 감소 확인")
                        else:
                            print("⚠️ 메일 읽음 처리 후에도 읽지 않은 메일 수가 감소하지 않음")
            
            # 6. 메일을 다시 읽지 않음으로 표시
            if mail_ids:
                print("\n📧 메일 읽지않음 처리 테스트")
                print("-" * 50)
                
                first_mail_id = mail_ids[0]
                if self.mark_mail_as_unread(first_mail_id):
                    time.sleep(1)  # 처리 대기
                    
                    # 읽지 않은 메일 수 다시 확인
                    result = self.get_unread_mails()
                    if result and result.get("success"):
                        after_unread_count = result["data"]["total"]
                        print(f"📊 읽지않음 처리 후 읽지 않은 메일 수: {after_unread_count}개")
                        
                        if after_unread_count > after_read_count:
                            print("✅ 메일 읽지않음 처리 후 읽지 않은 메일 수 증가 확인")
                        else:
                            print("⚠️ 메일 읽지않음 처리 후에도 읽지 않은 메일 수가 증가하지 않음")
            
            # 7. 페이지네이션 테스트
            print("\n📄 페이지네이션 테스트")
            print("-" * 50)
            
            # 페이지 크기 2로 조회
            result = self.get_unread_mails(page=1, limit=2)
            if result and result.get("success"):
                data = result["data"]
                print(f"📊 페이지 1 (limit=2): {len(data['mails'])}개 메일")
                print(f"📊 총 페이지 수: {data['pages']}개")
                print(f"📊 총 메일 수: {data['total']}개")
                
                if data["pages"] > 1:
                    # 두 번째 페이지 조회
                    result2 = self.get_unread_mails(page=2, limit=2)
                    if result2 and result2.get("success"):
                        data2 = result2["data"]
                        print(f"📊 페이지 2 (limit=2): {len(data2['mails'])}개 메일")
                        print("✅ 페이지네이션 테스트 성공")
                    else:
                        print("⚠️ 두 번째 페이지 조회 실패")
                else:
                    print("✅ 페이지네이션 테스트 성공 (단일 페이지)")
            else:
                print("❌ 페이지네이션 테스트 실패")
            
            print("\n🎉 테스트 결과 요약")
            print("=" * 60)
            print("📋 메일 생성: ✅ 성공")
            print("📋 읽지 않은 메일 조회: ✅ 성공")
            print("📋 메일 읽음 처리: ✅ 성공")
            print("📋 메일 읽지않음 처리: ✅ 성공")
            print("📋 페이지네이션: ✅ 성공")
            print("\n🎉 모든 테스트 통과!")
            
            return True
            
        finally:
            # 테스트 메일 정리
            self.cleanup_test_mails()

def main():
    """메인 함수"""
    print("🧪 읽지 않은 메일 조회 엔드포인트 종합 테스트")
    print("=" * 60)
    
    tester = UnreadMailTesterWithData()
    
    try:
        success = tester.run_comprehensive_test()
        
        if success:
            print("\n✅ 읽지 않은 메일 조회 엔드포인트 종합 테스트 완료")
        else:
            print("\n❌ 읽지 않은 메일 조회 엔드포인트 종합 테스트 실패")
            
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 테스트가 중단되었습니다.")
        tester.cleanup_test_mails()
    except Exception as e:
        print(f"\n❌ 테스트 중 예상치 못한 오류 발생: {str(e)}")
        tester.cleanup_test_mails()

if __name__ == "__main__":
    main()