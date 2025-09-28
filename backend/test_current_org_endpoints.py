#!/usr/bin/env python3
"""
현재 조직 통계 및 설정 엔드포인트 테스트

조직 라우터의 현재 조직 관련 엔드포인트들을 테스트합니다.
"""

import asyncio
import httpx
import json
from datetime import datetime

# 테스트 설정
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test.admin@example.com"
TEST_PASSWORD = "admin123"

class CurrentOrgEndpointTester:
    def __init__(self):
        self.access_token = None
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def login(self):
        """로그인하여 액세스 토큰 획득"""
        try:
            login_data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            response = await self.client.post(
                f"{BASE_URL}/api/v1/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get("access_token")
                print(f"✅ 로그인 성공: {TEST_EMAIL}")
                return True
            else:
                print(f"❌ 로그인 실패: {response.status_code}")
                print(f"응답: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 로그인 오류: {str(e)}")
            return False
    
    def get_auth_headers(self):
        """인증 헤더 반환"""
        if not self.access_token:
            return {}
        return {"Authorization": f"Bearer {self.access_token}"}
    
    async def test_current_organization_info(self):
        """현재 조직 정보 조회 테스트"""
        try:
            print("\n🏢 현재 조직 정보 조회 테스트")
            
            response = await self.client.get(
                f"{BASE_URL}/api/v1/organizations/current",
                headers=self.get_auth_headers()
            )
            
            print(f"상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 현재 조직 정보 조회 성공")
                print(f"조직 ID: {data.get('org_id')}")
                print(f"조직명: {data.get('name')}")
                print(f"도메인: {data.get('domain')}")
                print(f"활성 상태: {data.get('is_active')}")
                return True
            else:
                print(f"❌ 현재 조직 정보 조회 실패")
                print(f"응답: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 현재 조직 정보 조회 오류: {str(e)}")
            return False
    
    async def test_current_organization_stats(self):
        """현재 조직 통계 조회 테스트"""
        try:
            print("\n📊 현재 조직 통계 조회 테스트")
            
            response = await self.client.get(
                f"{BASE_URL}/api/v1/organizations/current/stats",
                headers=self.get_auth_headers()
            )
            
            print(f"상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 현재 조직 통계 조회 성공")
                print(f"조직 ID: {data.get('org_id')}")
                print(f"총 사용자 수: {data.get('total_users')}")
                print(f"활성 사용자 수: {data.get('active_users')}")
                print(f"메일 사용자 수: {data.get('mail_users')}")
                print(f"저장 공간 사용량: {data.get('storage_used_mb')} MB")
                print(f"저장 공간 사용률: {data.get('storage_usage_percent')}%")
                return True
            else:
                print(f"❌ 현재 조직 통계 조회 실패")
                print(f"응답: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 현재 조직 통계 조회 오류: {str(e)}")
            return False
    
    async def test_current_organization_settings(self):
        """현재 조직 설정 조회 테스트"""
        try:
            print("\n⚙️ 현재 조직 설정 조회 테스트")
            
            response = await self.client.get(
                f"{BASE_URL}/api/v1/organizations/current/settings",
                headers=self.get_auth_headers()
            )
            
            print(f"상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 현재 조직 설정 조회 성공")
                print(f"조직 정보:")
                org_info = data.get('organization', {})
                print(f"  - 조직 ID: {org_info.get('org_id')}")
                print(f"  - 조직명: {org_info.get('name')}")
                
                print(f"설정 정보:")
                settings = data.get('settings', {})
                print(f"  - 메일 보관 기간: {settings.get('mail_retention_days')} 일")
                print(f"  - 첨부파일 최대 크기: {settings.get('max_attachment_size_mb')} MB")
                print(f"  - 자동 백업 활성화: {settings.get('auto_backup_enabled')}")
                print(f"  - 스팸 필터 활성화: {settings.get('spam_filter_enabled')}")
                return True
            else:
                print(f"❌ 현재 조직 설정 조회 실패")
                print(f"응답: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 현재 조직 설정 조회 오류: {str(e)}")
            return False
    
    async def test_specific_org_stats(self, org_id: str):
        """특정 조직 통계 조회 테스트"""
        try:
            print(f"\n📊 특정 조직 통계 조회 테스트 (org_id: {org_id})")
            
            response = await self.client.get(
                f"{BASE_URL}/api/v1/organizations/{org_id}/stats",
                headers=self.get_auth_headers()
            )
            
            print(f"상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 특정 조직 통계 조회 성공")
                print(f"조직 ID: {data.get('org_id')}")
                print(f"총 사용자 수: {data.get('total_users')}")
                print(f"활성 사용자 수: {data.get('active_users')}")
                print(f"메일 사용자 수: {data.get('mail_users')}")
                print(f"저장 공간 사용량: {data.get('storage_used_mb')} MB")
                return True
            else:
                print(f"❌ 특정 조직 통계 조회 실패")
                print(f"응답: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 특정 조직 통계 조회 오류: {str(e)}")
            return False
    
    async def test_specific_org_settings(self, org_id: str):
        """특정 조직 설정 조회 테스트"""
        try:
            print(f"\n⚙️ 특정 조직 설정 조회 테스트 (org_id: {org_id})")
            
            response = await self.client.get(
                f"{BASE_URL}/api/v1/organizations/{org_id}/settings",
                headers=self.get_auth_headers()
            )
            
            print(f"상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 특정 조직 설정 조회 성공")
                print(f"조직 정보:")
                org_info = data.get('organization', {})
                print(f"  - 조직 ID: {org_info.get('org_id')}")
                print(f"  - 조직명: {org_info.get('name')}")
                
                print(f"설정 정보:")
                settings = data.get('settings', {})
                print(f"  - 메일 보관 기간: {settings.get('mail_retention_days')} 일")
                print(f"  - 첨부파일 최대 크기: {settings.get('max_attachment_size_mb')} MB")
                return True
            else:
                print(f"❌ 특정 조직 설정 조회 실패")
                print(f"응답: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 특정 조직 설정 조회 오류: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 현재 조직 엔드포인트 테스트 시작")
        print(f"테스트 시간: {datetime.now()}")
        print(f"기본 URL: {BASE_URL}")
        print(f"테스트 사용자: {TEST_EMAIL}")
        
        # 로그인
        if not await self.login():
            print("❌ 로그인 실패로 테스트를 중단합니다.")
            return
        
        # 테스트 실행
        results = []
        
        # 현재 조직 정보 조회
        results.append(await self.test_current_organization_info())
        
        # 현재 조직 통계 조회
        results.append(await self.test_current_organization_stats())
        
        # 현재 조직 설정 조회
        results.append(await self.test_current_organization_settings())
        
        # 특정 조직 통계 조회 (A001)
        results.append(await self.test_specific_org_stats("A001"))
        
        # 특정 조직 설정 조회 (A001)
        results.append(await self.test_specific_org_settings("A001"))
        
        # 결과 요약
        print(f"\n📋 테스트 결과 요약")
        print(f"총 테스트: {len(results)}")
        print(f"성공: {sum(results)}")
        print(f"실패: {len(results) - sum(results)}")
        
        if all(results):
            print("✅ 모든 테스트가 성공했습니다!")
        else:
            print("❌ 일부 테스트가 실패했습니다.")
    
    async def close(self):
        """클라이언트 종료"""
        await self.client.aclose()

async def main():
    """메인 함수"""
    tester = CurrentOrgEndpointTester()
    try:
        await tester.run_all_tests()
    finally:
        await tester.close()

if __name__ == "__main__":
    asyncio.run(main())