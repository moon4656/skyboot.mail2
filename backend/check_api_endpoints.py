#!/usr/bin/env python3
"""
FastAPI OpenAPI 스키마를 통한 엔드포인트 등록 확인 스크립트
"""

import requests
import json
from datetime import datetime

def check_api_endpoints():
    """FastAPI OpenAPI 스키마를 통해 엔드포인트 등록 상태 확인"""
    print("🔍 FastAPI 엔드포인트 등록 상태 확인")
    print("=" * 60)
    
    try:
        # OpenAPI 스키마 가져오기
        response = requests.get("http://localhost:8000/openapi.json", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ OpenAPI 스키마 가져오기 실패: {response.status_code}")
            return
        
        openapi_data = response.json()
        paths = openapi_data.get("paths", {})
        
        print(f"✅ OpenAPI 스키마 가져오기 성공")
        print(f"📊 총 등록된 경로 수: {len(paths)}")
        print()
        
        # mail_convenience_router 엔드포인트 확인
        convenience_endpoints = [
            "/api/v1/mail/search/suggestions",
            "/api/v1/mail/search", 
            "/api/v1/mail/stats",
            "/api/v1/mail/unread",
            "/api/v1/mail/starred"
        ]
        
        # mail_advanced_router 엔드포인트 확인
        advanced_endpoints = [
            "/api/v1/mail/folders",
            "/api/v1/mail/analytics",
            "/api/v1/mail/backup"
        ]
        
        print("📧 Mail Convenience Router 엔드포인트 확인:")
        print("-" * 50)
        for endpoint in convenience_endpoints:
            if endpoint in paths:
                methods = list(paths[endpoint].keys())
                print(f"✅ {endpoint} - 메서드: {', '.join(methods)}")
            else:
                print(f"❌ {endpoint} - 등록되지 않음")
        
        print()
        print("📁 Mail Advanced Router 엔드포인트 확인:")
        print("-" * 50)
        for endpoint in advanced_endpoints:
            if endpoint in paths:
                methods = list(paths[endpoint].keys())
                print(f"✅ {endpoint} - 메서드: {', '.join(methods)}")
            else:
                print(f"❌ {endpoint} - 등록되지 않음")
        
        print()
        print("🔍 모든 메일 관련 엔드포인트 목록:")
        print("-" * 50)
        mail_endpoints = [path for path in paths.keys() if "/mail/" in path]
        mail_endpoints.sort()
        
        for endpoint in mail_endpoints:
            methods = list(paths[endpoint].keys())
            print(f"📍 {endpoint} - {', '.join(methods)}")
        
        print()
        print(f"📊 메일 관련 엔드포인트 총 {len(mail_endpoints)}개 등록됨")
        
        # 결과 저장
        result = {
            "timestamp": datetime.now().isoformat(),
            "total_endpoints": len(paths),
            "mail_endpoints_count": len(mail_endpoints),
            "convenience_router_status": {
                endpoint: endpoint in paths for endpoint in convenience_endpoints
            },
            "advanced_router_status": {
                endpoint: endpoint in paths for endpoint in advanced_endpoints
            },
            "all_mail_endpoints": mail_endpoints
        }
        
        with open('api_endpoints_check.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 상세 결과가 'api_endpoints_check.json' 파일에 저장되었습니다.")
        
        # 404 오류 관련 결론
        missing_convenience = sum(1 for endpoint in convenience_endpoints if endpoint not in paths)
        missing_advanced = sum(1 for endpoint in advanced_endpoints if endpoint not in paths)
        
        print()
        print("🎯 404 오류 분석 결과:")
        print("-" * 50)
        if missing_convenience == 0 and missing_advanced == 0:
            print("✅ 모든 엔드포인트가 정상적으로 등록되어 있습니다.")
            print("✅ 테스트 보고서의 404 오류는 일시적 문제였거나 다른 원인으로 추정됩니다.")
        else:
            print(f"❌ mail_convenience_router에서 {missing_convenience}개 엔드포인트 누락")
            print(f"❌ mail_advanced_router에서 {missing_advanced}개 엔드포인트 누락")
        
    except requests.exceptions.ConnectionError:
        print("❌ 서버 연결 실패 - 서버가 실행되고 있는지 확인하세요.")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {str(e)}")

if __name__ == "__main__":
    check_api_endpoints()