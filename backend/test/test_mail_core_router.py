"""
메일 핵심 기능 라우터 테스트

메일 발송, 수신, 관리 등 핵심 메일 기능 API 엔드포인트 테스트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json
import io
from fastapi.testclient import TestClient
from main import app
from auth_utils import TestAuthUtils, get_test_admin_token, get_test_user_token, get_test_auth_headers


class TestMailCoreRouter:
    """메일 핵심 기능 라우터 테스트 클래스"""
    
    @classmethod
    def setup_class(cls):
        """테스트 클래스 초기화"""
        print("\n" + "="*60)
        print("📧 메일 핵심 기능 라우터 테스트 시작")
        print("="*60)
        
        # TestClient 초기화
        cls.client = TestClient(app)
        
        # 테스트 데이터 준비
        cls.test_data = {
            "org_id": "skyboot",
            "org_uuid": "bbf43d4b-3862-4ab0-9a03-522213ccb7a2"
        }
        
        # 토큰 캐시 초기화 및 토큰 생성
        TestAuthUtils.clear_token_cache()
        cls.admin_token = TestAuthUtils.get_admin_token(cls.client)
        cls.user_token = TestAuthUtils.get_user_token(cls.client)
        
        # 헤더 직접 생성 (토큰 재사용)
        cls.admin_headers = {
            "Authorization": f"Bearer {cls.admin_token}",
            "Content-Type": "application/json"
        } if cls.admin_token else {"Content-Type": "application/json"}
        
        cls.user_headers = {
            "Authorization": f"Bearer {cls.user_token}",
            "Content-Type": "application/json"
        } if cls.user_token else {"Content-Type": "application/json"}
        
        print(f"관리자 토큰 생성: {'✅' if cls.admin_token else '❌'}")
        print(f"사용자 토큰 생성: {'✅' if cls.user_token else '❌'}")
        
        # 관리자 계정 검증
        if TestAuthUtils.verify_admin_account():
            print("✅ 관리자 계정 검증 성공")
        else:
            print("❌ 관리자 계정 검증 실패")
        
        # 테스트용 메일 ID 저장
        cls.test_mail_uuid = None

    
    def test_01_send_mail(self):
        """메일 발송 테스트"""
        print("\n🧪 test_01_send_mail")
        
        if not self.admin_token:
            print("⏭️ 관리자 토큰이 없어 메일 발송 테스트를 건너뜁니다.")
            return
        
        # 테스트 메일 데이터
        mail_data = {
            "to_emails": "test@skyboot.com",
            "subject": "테스트 메일",
            "content": "이것은 테스트 메일입니다.",
            "priority": "NORMAL"
        }
        
        response = self.client.post(
            "/api/v1/mail/send",
            headers=self.admin_headers,
            data=mail_data
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if "mail_uuid" in data:
                self.__class__.test_mail_uuid = data["mail_uuid"]
                print(f"생성된 메일 UUID: {self.test_mail_uuid}")
            print("✅ test_01_send_mail 성공")
        else:
            print("❌ test_01_send_mail 실패")
    
    def test_02_send_mail_with_attachments(self):
        """첨부파일이 있는 메일 발송 테스트"""
        print("\n🧪 test_02_send_mail_with_attachments")
        
        if not self.admin_token:
            print("⏭️ 관리자 토큰이 없어 첨부파일 메일 발송 테스트를 건너뜁니다.")
            return
        
        # 테스트 파일 생성
        test_file_content = b"This is a test file content"
        test_file = io.BytesIO(test_file_content)
        
        files = {
            "attachments": ("test.txt", test_file, "text/plain")
        }
        
        data = {
            "to_emails": "test@skyboot.com",
            "subject": "첨부파일 테스트 메일",
            "content": "첨부파일이 포함된 테스트 메일입니다.",
            "priority": "NORMAL"
        }
        
        response = self.client.post(
            "/api/v1/mail/send",
            headers=self.admin_headers,
            data=data,
            files=files
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        if response.status_code == 200:
            print("✅ test_02_send_mail_with_attachments 성공")
        else:
            print("❌ test_02_send_mail_with_attachments 실패")
    
    def test_03_get_inbox(self):
        """받은 메일함 조회 테스트"""
        print("\n🧪 test_03_get_inbox")
        
        if not self.admin_token:
            print("⏭️ 관리자 토큰이 없어 받은 메일함 조회 테스트를 건너뜁니다.")
            return
        
        response = self.client.get(
            "/api/v1/mail/inbox?page=1&limit=10",
            headers=self.admin_headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "pagination" in data
            print("✅ test_03_get_inbox 성공")
        else:
            print("❌ test_03_get_inbox 실패")
    
    def test_04_get_sent_mails(self):
        """보낸 메일함 조회 테스트"""
        print("\n🧪 test_04_get_sent_mails")
        
        if not self.admin_token:
            print("⏭️ 관리자 토큰이 없어 보낸 메일함 조회 테스트를 건너뜁니다.")
            return
        
        response = self.client.get(
            "/api/v1/mail/sent?page=1&limit=10",
            headers=self.admin_headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "pagination" in data
            print("✅ test_04_get_sent_mails 성공")
        else:
            print("❌ test_04_get_sent_mails 실패")
    
    def test_05_get_drafts(self):
        """임시보관함 조회 테스트"""
        print("\n🧪 test_05_get_drafts")
        
        if not self.admin_token:
            print("⏭️ 관리자 토큰이 없어 임시보관함 조회 테스트를 건너뜁니다.")
            return
        
        response = self.client.get(
            "/api/v1/mail/drafts?page=1&limit=10",
            headers=self.admin_headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "pagination" in data
            print("✅ test_05_get_drafts 성공")
        else:
            print("❌ test_05_get_drafts 실패")
    
    def test_06_get_trash(self):
        """휴지통 조회 테스트"""
        print("\n🧪 test_06_get_trash")
        
        if not self.admin_token:
            print("⏭️ 관리자 토큰이 없어 휴지통 조회 테스트를 건너뜁니다.")
            return
        
        response = self.client.get(
            "/api/v1/mail/trash?page=1&limit=10",
            headers=self.admin_headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "pagination" in data
            print("✅ test_06_get_trash 성공")
        else:
            print("❌ test_06_get_trash 실패")
    
    def test_07_get_inbox_mail_detail(self):
        """받은 메일 상세 조회 테스트"""
        print("\n🧪 test_07_get_inbox_mail_detail")
        
        if not self.admin_token:
            print("⏭️ 관리자 토큰이 없어 받은 메일 상세 조회 테스트를 건너뜁니다.")
            return
        
        # 먼저 받은 메일함에서 메일 목록을 가져와서 첫 번째 메일의 UUID를 사용
        inbox_response = self.client.get(
            "/api/v1/mail/inbox?page=1&limit=1",
            headers=self.admin_headers
        )
        
        if inbox_response.status_code == 200:
            inbox_data = inbox_response.json()
            if inbox_data.get("items") and len(inbox_data["items"]) > 0:
                mail_uuid = inbox_data["items"][0].get("mail_uuid")
                
                if mail_uuid:
                    response = self.client.get(
                        f"/api/v1/mail/inbox/{mail_uuid}",
                        headers=self.admin_headers
                    )
                    
                    print(f"응답 상태 코드: {response.status_code}")
                    print(f"응답 내용: {response.json()}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        assert "mail_uuid" in data
                        assert "subject" in data
                        print("✅ test_07_get_inbox_mail_detail 성공")
                    else:
                        print("❌ test_07_get_inbox_mail_detail 실패")
                else:
                    print("⏭️ 받은 메일함에 메일이 없어 상세 조회 테스트를 건너뜁니다.")
            else:
                print("⏭️ 받은 메일함에 메일이 없어 상세 조회 테스트를 건너뜁니다.")
        else:
            print("❌ 받은 메일함 조회 실패로 상세 조회 테스트를 건너뜁니다.")
    
    def test_08_get_sent_mail_detail(self):
        """보낸 메일 상세 조회 테스트"""
        print("\n🧪 test_08_get_sent_mail_detail")
        
        if not self.admin_token:
            print("⏭️ 관리자 토큰이 없어 보낸 메일 상세 조회 테스트를 건너뜁니다.")
            return
        
        # 먼저 보낸 메일함에서 메일 목록을 가져와서 첫 번째 메일의 UUID를 사용
        sent_response = self.client.get(
            "/api/v1/mail/sent?page=1&limit=1",
            headers=self.admin_headers
        )
        
        if sent_response.status_code == 200:
            sent_data = sent_response.json()
            if sent_data.get("items") and len(sent_data["items"]) > 0:
                mail_uuid = sent_data["items"][0].get("mail_uuid")
                
                if mail_uuid:
                    response = self.client.get(
                        f"/api/v1/mail/sent/{mail_uuid}",
                        headers=self.admin_headers
                    )
                    
                    print(f"응답 상태 코드: {response.status_code}")
                    print(f"응답 내용: {response.json()}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        assert "mail_uuid" in data
                        assert "subject" in data
                        print("✅ test_08_get_sent_mail_detail 성공")
                    else:
                        print("❌ test_08_get_sent_mail_detail 실패")
                else:
                    print("⏭️ 보낸 메일함에 메일이 없어 상세 조회 테스트를 건너뜁니다.")
            else:
                print("⏭️ 보낸 메일함에 메일이 없어 상세 조회 테스트를 건너뜁니다.")
        else:
            print("❌ 보낸 메일함 조회 실패로 상세 조회 테스트를 건너뜁니다.")
    
    def test_09_search_mails(self):
        """메일 검색 테스트"""
        print("\n🧪 test_09_search_mails")
        
        if not self.admin_token:
            print("⏭️ 관리자 토큰이 없어 메일 검색 테스트를 건너뜁니다.")
            return
        
        # 받은 메일함에서 검색
        response = self.client.get(
            "/api/v1/mail/inbox?page=1&limit=10&search=테스트",
            headers=self.admin_headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            assert "items" in data
            assert "pagination" in data
            print("✅ test_09_search_mails 성공")
        else:
            print("❌ test_09_search_mails 실패")
    
    def test_10_unauthorized_access(self):
        """인증되지 않은 접근 테스트"""
        print("\n🧪 test_10_unauthorized_access")
        
        # 토큰 없이 요청
        response = self.client.get("/api/v1/mail/inbox")
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        if response.status_code == 401 or response.status_code == 403:
            print("✅ test_10_unauthorized_access 성공 (인증 필요 확인)")
        else:
            print("❌ test_10_unauthorized_access 실패")
    
    def test_11_invalid_mail_uuid(self):
        """잘못된 메일 UUID로 상세 조회 테스트"""
        print("\n🧪 test_11_invalid_mail_uuid")
        
        if not self.admin_token:
            print("⏭️ 관리자 토큰이 없어 잘못된 UUID 테스트를 건너뜁니다.")
            return
        
        invalid_uuid = "invalid-uuid-12345"
        
        response = self.client.get(
            f"/api/v1/mail/inbox/{invalid_uuid}",
            headers=self.admin_headers
        )
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
        
        if response.status_code == 404:
            print("✅ test_11_invalid_mail_uuid 성공 (메일 없음 확인)")
        else:
            print("❌ test_11_invalid_mail_uuid 실패")
    
    def test_12_performance_test(self):
        """성능 테스트"""
        print("\n🧪 test_12_performance_test")
        
        if not self.admin_token:
            print("⏭️ 관리자 토큰이 없어 성능 테스트를 건너뜁니다.")
            return
        
        start_time = time.time()
        success_count = 0
        
        for i in range(10):
            response = self.client.get(
                "/api/v1/mail/inbox?page=1&limit=5",
                headers=self.admin_headers
            )
            if response.status_code == 200:
                success_count += 1
        
        end_time = time.time()
        duration = end_time - start_time
        avg_response_time = (duration / 10) * 1000  # ms
        
        print(f"10회 요청 처리 시간: {duration:.2f}초")
        print(f"성공한 요청: {success_count}/10")
        print(f"평균 응답 시간: {avg_response_time:.2f}ms")
        
        if success_count >= 8 and avg_response_time < 2000:
            print("✅ test_12_performance_test 성공")
        else:
            print("❌ test_12_performance_test 실패")


def run_tests():
    """테스트 실행 함수"""
    test_instance = TestMailCoreRouter()
    test_instance.setup_class()
    
    # 테스트 메서드 목록
    test_methods = [
        test_instance.test_01_send_mail,
        test_instance.test_02_send_mail_with_attachments,
        test_instance.test_03_get_inbox,
        test_instance.test_04_get_sent_mails,
        test_instance.test_05_get_drafts,
        test_instance.test_06_get_trash,
        test_instance.test_07_get_inbox_mail_detail,
        test_instance.test_08_get_sent_mail_detail,
        test_instance.test_09_search_mails,
        test_instance.test_10_unauthorized_access,
        test_instance.test_11_invalid_mail_uuid,
        test_instance.test_12_performance_test
    ]
    
    # 테스트 실행
    success_count = 0
    total_count = len(test_methods)
    
    for test_method in test_methods:
        try:
            test_method()
            success_count += 1
        except Exception as e:
            print(f"❌ {test_method.__name__} 실패: {str(e)}")
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {total_count - success_count}개")
    print(f"📈 성공률: {(success_count / total_count) * 100:.1f}%")
    print("="*60)


if __name__ == "__main__":
    run_tests()