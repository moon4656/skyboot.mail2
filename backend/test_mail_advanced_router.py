#!/usr/bin/env python3
"""
Mail Advanced Router 종합 테스트 스크립트
- 폴더 관리 기능 테스트
- 백업/복원 기능 테스트  
- 검색/필터링 기능 테스트
- 분석 기능 테스트
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# 테스트 설정
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# 테스트 사용자 정보
TEST_USER = {
    "email": "test@skyboot.kr",
    "password": "testpassword123"
}

class MailAdvancedRouterTester:
    def __init__(self):
        self.token = None
        self.test_results = {
            "folder_management": {},
            "backup_restore": {},
            "search_filter": {},
            "analytics": {},
            "summary": {}
        }
        self.created_folder_uuid = None
        self.backup_id = None
        
    def login(self) -> bool:
        """사용자 로그인"""
        try:
            print("🔐 로그인 테스트 시작...")
            
            login_data = {
                "email": TEST_USER["email"],
                "password": TEST_USER["password"]
            }
            
            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                print(f"✅ 로그인 성공 - 토큰: {self.token[:20]}...")
                return True
            else:
                print(f"❌ 로그인 실패 - 상태코드: {response.status_code}, 응답: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 로그인 오류: {str(e)}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """인증 헤더 반환"""
        return {"Authorization": f"Bearer {self.token}"}
    
    # ===== 폴더 관리 테스트 =====
    
    def test_get_folders(self) -> bool:
        """폴더 목록 조회 테스트"""
        try:
            print("\n📁 폴더 목록 조회 테스트...")
            
            response = requests.get(
                f"{BASE_URL}{API_PREFIX}/mail/folders",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                folders = data.get("folders", [])
                print(f"✅ 폴더 목록 조회 성공 - 폴더 수: {len(folders)}")
                
                # 기본 폴더 확인
                folder_types = [folder.get("folder_type") for folder in folders]
                expected_types = ["inbox", "sent", "drafts", "trash"]
                
                for expected_type in expected_types:
                    if expected_type in folder_types:
                        print(f"  ✓ {expected_type} 폴더 존재")
                    else:
                        print(f"  ⚠️ {expected_type} 폴더 없음")
                
                self.test_results["folder_management"]["get_folders"] = {
                    "status": "success",
                    "folder_count": len(folders),
                    "folders": folders
                }
                return True
            else:
                print(f"❌ 폴더 목록 조회 실패 - 상태코드: {response.status_code}")
                self.test_results["folder_management"]["get_folders"] = {
                    "status": "failed",
                    "error": response.text
                }
                return False
                
        except Exception as e:
            print(f"❌ 폴더 목록 조회 오류: {str(e)}")
            self.test_results["folder_management"]["get_folders"] = {
                "status": "error",
                "error": str(e)
            }
            return False
    
    def test_create_folder(self) -> bool:
        """폴더 생성 테스트"""
        try:
            print("\n📁 폴더 생성 테스트...")
            
            folder_data = {
                "name": f"테스트폴더_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "folder_type": "custom"
            }
            
            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/mail/folders",
                json=folder_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                self.created_folder_uuid = data.get("folder_uuid")
                print(f"✅ 폴더 생성 성공 - 폴더명: {data.get('name')}, UUID: {self.created_folder_uuid}")
                
                self.test_results["folder_management"]["create_folder"] = {
                    "status": "success",
                    "folder_data": data
                }
                return True
            else:
                print(f"❌ 폴더 생성 실패 - 상태코드: {response.status_code}, 응답: {response.text}")
                self.test_results["folder_management"]["create_folder"] = {
                    "status": "failed",
                    "error": response.text
                }
                return False
                
        except Exception as e:
            print(f"❌ 폴더 생성 오류: {str(e)}")
            self.test_results["folder_management"]["create_folder"] = {
                "status": "error",
                "error": str(e)
            }
            return False
    
    def test_update_folder(self) -> bool:
        """폴더 수정 테스트"""
        if not self.created_folder_uuid:
            print("⚠️ 폴더 수정 테스트 건너뜀 - 생성된 폴더 없음")
            return False
            
        try:
            print("\n📁 폴더 수정 테스트...")
            
            update_data = {
                "name": f"수정된폴더_{datetime.now().strftime('%H%M%S')}"
            }
            
            response = requests.put(
                f"{BASE_URL}{API_PREFIX}/mail/folders/{self.created_folder_uuid}",
                json=update_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 폴더 수정 성공 - 새 이름: {data.get('name')}")
                
                self.test_results["folder_management"]["update_folder"] = {
                    "status": "success",
                    "updated_data": data
                }
                return True
            else:
                print(f"❌ 폴더 수정 실패 - 상태코드: {response.status_code}, 응답: {response.text}")
                self.test_results["folder_management"]["update_folder"] = {
                    "status": "failed",
                    "error": response.text
                }
                return False
                
        except Exception as e:
            print(f"❌ 폴더 수정 오류: {str(e)}")
            self.test_results["folder_management"]["update_folder"] = {
                "status": "error",
                "error": str(e)
            }
            return False
    
    def test_delete_folder(self) -> bool:
        """폴더 삭제 테스트"""
        if not self.created_folder_uuid:
            print("⚠️ 폴더 삭제 테스트 건너뜀 - 생성된 폴더 없음")
            return False
            
        try:
            print("\n🗑️ 폴더 삭제 테스트...")
            
            response = requests.delete(
                f"{BASE_URL}{API_PREFIX}/mail/folders/{self.created_folder_uuid}",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 폴더 삭제 성공 - 메시지: {data.get('message')}")
                
                self.test_results["folder_management"]["delete_folder"] = {
                    "status": "success",
                    "response": data
                }
                return True
            else:
                print(f"❌ 폴더 삭제 실패 - 상태코드: {response.status_code}, 응답: {response.text}")
                self.test_results["folder_management"]["delete_folder"] = {
                    "status": "failed",
                    "error": response.text
                }
                return False
                
        except Exception as e:
            print(f"❌ 폴더 삭제 오류: {str(e)}")
            self.test_results["folder_management"]["delete_folder"] = {
                "status": "error",
                "error": str(e)
            }
            return False
    
    # ===== 백업/복원 테스트 =====
    
    def test_create_backup(self) -> bool:
        """메일 백업 생성 테스트"""
        try:
            print("\n💾 메일 백업 생성 테스트...")
            
            # 백업 파라미터
            params = {
                "include_attachments": False,
                "date_from": (datetime.now() - timedelta(days=30)).isoformat(),
                "date_to": datetime.now().isoformat()
            }
            
            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/mail/backup",
                params=params,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                self.backup_id = data.get("backup_id")
                print(f"✅ 백업 생성 성공 - 백업 ID: {self.backup_id}")
                print(f"  📊 백업된 메일 수: {data.get('mail_count', 0)}")
                print(f"  📁 백업 파일: {data.get('backup_filename')}")
                
                self.test_results["backup_restore"]["create_backup"] = {
                    "status": "success",
                    "backup_data": data
                }
                return True
            else:
                print(f"❌ 백업 생성 실패 - 상태코드: {response.status_code}, 응답: {response.text}")
                self.test_results["backup_restore"]["create_backup"] = {
                    "status": "failed",
                    "error": response.text
                }
                return False
                
        except Exception as e:
            print(f"❌ 백업 생성 오류: {str(e)}")
            self.test_results["backup_restore"]["create_backup"] = {
                "status": "error",
                "error": str(e)
            }
            return False
    
    def test_download_backup(self) -> bool:
        """백업 파일 다운로드 테스트"""
        if not self.backup_id:
            print("⚠️ 백업 다운로드 테스트 건너뜀 - 백업 ID 없음")
            return False
            
        try:
            print("\n📥 백업 파일 다운로드 테스트...")
            
            response = requests.get(
                f"{BASE_URL}{API_PREFIX}/mail/backup/{self.backup_id}/download",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                content_length = len(response.content)
                print(f"✅ 백업 다운로드 성공 - 파일 크기: {content_length} bytes")
                
                self.test_results["backup_restore"]["download_backup"] = {
                    "status": "success",
                    "file_size": content_length
                }
                return True
            else:
                print(f"❌ 백업 다운로드 실패 - 상태코드: {response.status_code}")
                self.test_results["backup_restore"]["download_backup"] = {
                    "status": "failed",
                    "error": response.text
                }
                return False
                
        except Exception as e:
            print(f"❌ 백업 다운로드 오류: {str(e)}")
            self.test_results["backup_restore"]["download_backup"] = {
                "status": "error",
                "error": str(e)
            }
            return False
    
    # ===== 검색/필터링 테스트 =====
    
    def test_search_mails(self) -> bool:
        """메일 검색 테스트"""
        try:
            print("\n🔍 메일 검색 테스트...")
            
            # 다양한 검색 조건 테스트 (POST 방식)
            search_tests = [
                {"query": "test", "search_type": "all", "description": "키워드 검색"},
                {"query": "test@", "search_type": "sender", "description": "발신자 검색"},
                {"query": "테스트", "search_type": "subject", "description": "제목 검색"},
                {"query": "important", "search_type": "content", "description": "내용 검색"}
            ]
            
            search_results = []
            
            for test_case in search_tests:
                print(f"  🔍 {test_case['description']} 테스트...")
                
                search_data = {
                    "query": test_case["query"],
                    "search_type": test_case["search_type"],
                    "limit": 10,
                    "page": 1
                }
                
                response = requests.post(
                    f"{BASE_URL}{API_PREFIX}/mail/search",
                    json=search_data,
                    headers=self.get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    mail_count = len(data.get("mails", []))
                    print(f"    ✅ 성공 - 검색 결과: {mail_count}개")
                    
                    search_results.append({
                        "test": test_case["description"],
                        "status": "success",
                        "result_count": mail_count
                    })
                else:
                    print(f"    ❌ 실패 - 상태코드: {response.status_code}")
                    search_results.append({
                        "test": test_case["description"],
                        "status": "failed",
                        "error": response.text
                    })
            
            # 검색 자동완성 테스트
            print("  🔍 검색 자동완성 테스트...")
            suggestions_response = requests.get(
                f"{BASE_URL}{API_PREFIX}/mail/search/suggestions",
                params={"query": "test", "limit": 5},
                headers=self.get_headers()
            )
            
            if suggestions_response.status_code == 200:
                suggestions_data = suggestions_response.json()
                suggestions_count = len(suggestions_data.get("suggestions", []))
                print(f"    ✅ 자동완성 성공 - 제안 수: {suggestions_count}개")
                search_results.append({
                    "test": "검색 자동완성",
                    "status": "success",
                    "result_count": suggestions_count
                })
            else:
                print(f"    ❌ 자동완성 실패 - 상태코드: {suggestions_response.status_code}")
                search_results.append({
                    "test": "검색 자동완성",
                    "status": "failed",
                    "error": suggestions_response.text
                })
            
            self.test_results["search_filter"]["search_mails"] = {
                "status": "completed",
                "results": search_results
            }
            
            return True
            
        except Exception as e:
            print(f"❌ 메일 검색 오류: {str(e)}")
            self.test_results["search_filter"]["search_mails"] = {
                "status": "error",
                "error": str(e)
            }
            return False
    
    def test_filter_mails(self) -> bool:
        """메일 필터링 테스트"""
        try:
            print("\n🔍 메일 필터링 테스트...")
            
            # 다양한 필터 조건 테스트 (convenience 라우터 사용)
            filter_tests = [
                {"endpoint": "unread", "description": "읽지 않은 메일 필터"},
                {"endpoint": "starred", "description": "중요 메일 필터"},
                {"endpoint": "recent", "description": "최근 메일 필터"}
            ]
            
            filter_results = []
            
            for test_case in filter_tests:
                print(f"  🔍 {test_case['description']} 테스트...")
                
                response = requests.get(
                    f"{BASE_URL}{API_PREFIX}/mail/{test_case['endpoint']}",
                    params={"page": 1, "limit": 10},
                    headers=self.get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    mail_count = len(data.get("mails", []))
                    print(f"    ✅ 성공 - 필터 결과: {mail_count}개")
                    
                    filter_results.append({
                        "test": test_case["description"],
                        "status": "success",
                        "result_count": mail_count
                    })
                else:
                    print(f"    ❌ 실패 - 상태코드: {response.status_code}")
                    filter_results.append({
                        "test": test_case["description"],
                        "status": "failed",
                        "error": response.text
                    })
            
            # 폴더별 메일 조회 테스트
            print("  🔍 폴더별 메일 조회 테스트...")
            folder_response = requests.get(
                f"{BASE_URL}{API_PREFIX}/mail/folders",
                headers=self.get_headers()
            )
            
            if folder_response.status_code == 200:
                folders_data = folder_response.json()
                folders = folders_data.get("folders", [])
                
                if folders:
                    # 첫 번째 폴더의 메일 조회
                    first_folder = folders[0]
                    folder_uuid = first_folder.get("folder_uuid")
                    
                    mails_response = requests.get(
                        f"{BASE_URL}{API_PREFIX}/mail/folders/{folder_uuid}/mails",
                        params={"page": 1, "limit": 10},
                        headers=self.get_headers()
                    )
                    
                    if mails_response.status_code == 200:
                        mails_data = mails_response.json()
                        mail_count = len(mails_data.get("mails", []))
                        print(f"    ✅ 폴더별 조회 성공 - 메일 수: {mail_count}개")
                        filter_results.append({
                            "test": "폴더별 메일 조회",
                            "status": "success",
                            "result_count": mail_count
                        })
                    else:
                        print(f"    ❌ 폴더별 조회 실패 - 상태코드: {mails_response.status_code}")
                        filter_results.append({
                            "test": "폴더별 메일 조회",
                            "status": "failed",
                            "error": mails_response.text
                        })
                else:
                    print("    ⚠️ 폴더가 없어 폴더별 조회 테스트 건너뜀")
            
            self.test_results["search_filter"]["filter_mails"] = {
                "status": "completed",
                "results": filter_results
            }
            
            return True
            
        except Exception as e:
            print(f"❌ 메일 필터링 오류: {str(e)}")
            self.test_results["search_filter"]["filter_mails"] = {
                "status": "error",
                "error": str(e)
            }
            return False
    
    # ===== 분석 테스트 =====
    
    def test_analytics(self) -> bool:
        """메일 분석 테스트"""
        try:
            print("\n📊 메일 분석 테스트...")
            
            response = requests.get(
                f"{BASE_URL}{API_PREFIX}/mail/analytics",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 분석 데이터 조회 성공")
                print(f"  📧 총 메일 수: {data.get('total_mails', 0)}")
                print(f"  📤 보낸 메일: {data.get('sent_mails', 0)}")
                print(f"  📥 받은 메일: {data.get('received_mails', 0)}")
                print(f"  📎 첨부파일 수: {data.get('total_attachments', 0)}")
                print(f"  💾 사용 용량: {data.get('storage_used', 0)} MB")
                
                self.test_results["analytics"]["get_analytics"] = {
                    "status": "success",
                    "analytics_data": data
                }
                return True
            else:
                print(f"❌ 분석 데이터 조회 실패 - 상태코드: {response.status_code}")
                self.test_results["analytics"]["get_analytics"] = {
                    "status": "failed",
                    "error": response.text
                }
                return False
                
        except Exception as e:
            print(f"❌ 분석 데이터 조회 오류: {str(e)}")
            self.test_results["analytics"]["get_analytics"] = {
                "status": "error",
                "error": str(e)
            }
            return False
    
    # ===== 종합 테스트 실행 =====
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 Mail Advanced Router 종합 테스트 시작")
        print("=" * 60)
        
        start_time = time.time()
        
        # 로그인
        if not self.login():
            print("❌ 로그인 실패로 테스트 중단")
            return
        
        # 폴더 관리 테스트
        print("\n📁 폴더 관리 기능 테스트")
        print("-" * 40)
        self.test_get_folders()
        self.test_create_folder()
        self.test_update_folder()
        self.test_delete_folder()
        
        # 백업/복원 테스트
        print("\n💾 백업/복원 기능 테스트")
        print("-" * 40)
        self.test_create_backup()
        self.test_download_backup()
        
        # 검색/필터링 테스트
        print("\n🔍 검색/필터링 기능 테스트")
        print("-" * 40)
        self.test_search_mails()
        self.test_filter_mails()
        
        # 분석 테스트
        print("\n📊 분석 기능 테스트")
        print("-" * 40)
        self.test_analytics()
        
        # 결과 요약
        end_time = time.time()
        duration = end_time - start_time
        
        self.generate_summary(duration)
        self.save_results()
    
    def generate_summary(self, duration: float):
        """테스트 결과 요약 생성"""
        print("\n" + "=" * 60)
        print("📋 테스트 결과 요약")
        print("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        error_tests = 0
        
        for category, tests in self.test_results.items():
            if category == "summary":
                continue
                
            print(f"\n📂 {category.upper()}")
            for test_name, result in tests.items():
                total_tests += 1
                status = result.get("status", "unknown")
                
                if status == "success":
                    passed_tests += 1
                    print(f"  ✅ {test_name}: 성공")
                elif status == "failed":
                    failed_tests += 1
                    print(f"  ❌ {test_name}: 실패")
                elif status == "error":
                    error_tests += 1
                    print(f"  💥 {test_name}: 오류")
                else:
                    print(f"  ❓ {test_name}: {status}")
        
        print(f"\n📊 전체 통계:")
        print(f"  총 테스트: {total_tests}")
        print(f"  성공: {passed_tests}")
        print(f"  실패: {failed_tests}")
        print(f"  오류: {error_tests}")
        print(f"  성공률: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "  성공률: 0%")
        print(f"  실행 시간: {duration:.2f}초")
        
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "error_tests": error_tests,
            "success_rate": (passed_tests/total_tests*100) if total_tests > 0 else 0,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
    
    def save_results(self):
        """테스트 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mail_advanced_router_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 테스트 결과 저장: {filename}")

if __name__ == "__main__":
    tester = MailAdvancedRouterTester()
    tester.run_all_tests()