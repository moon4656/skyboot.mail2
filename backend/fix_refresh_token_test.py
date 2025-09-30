#!/usr/bin/env python3
"""
리프레시 토큰 저장 확인 테스트 수정 스크립트
"""

import sys
import os
import json
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

try:
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker
    
    from main import app
    from app.database.mail import get_db
    from app.model.user_model import User, RefreshToken
    from app.service.auth_service import AuthService
    
except ImportError as e:
    print(f"❌ 모듈 임포트 오류: {e}")
    sys.exit(1)

def test_refresh_token_storage():
    """리프레시 토큰 저장 확인 테스트"""
    
    print("🔍 리프레시 토큰 저장 확인 테스트 시작")
    print("=" * 60)
    
    # TestClient 생성
    client = TestClient(app)
    
    # 관리자 로그인 데이터
    admin_credentials = {
        "email": "admin@skyboot.com",
        "password": "Admin123!@#"
    }
    
    try:
        # 1. 로그인 요청
        print("📤 로그인 요청 전송...")
        response = client.post(
            "/api/v1/auth/login",
            json=admin_credentials
        )
        
        print(f"📥 응답 상태 코드: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ 로그인 실패: {response.text}")
            return
        
        # 2. 응답 데이터 확인
        response_data = response.json()
        print(f"📋 응답 데이터 키: {list(response_data.keys())}")
        
        access_token = response_data.get("access_token")
        refresh_token = response_data.get("refresh_token")
        
        print(f"🔑 액세스 토큰 존재: {'✅' if access_token else '❌'}")
        print(f"🔑 리프레시 토큰 존재: {'✅' if refresh_token else '❌'}")
        
        if not refresh_token:
            print("❌ 리프레시 토큰이 응답에 없습니다.")
            print(f"📋 전체 응답: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            return
        
        print(f"🔑 리프레시 토큰: {refresh_token[:50]}...")
        
        # 3. 데이터베이스에서 토큰 확인
        print("\n🔍 데이터베이스에서 토큰 확인...")
        
        db = next(get_db())
        try:
            # 토큰으로 직접 검색
            stored_token = db.query(RefreshToken).filter(
                RefreshToken.token == refresh_token
            ).first()
            
            if stored_token:
                print("✅ 데이터베이스에서 토큰 발견!")
                print(f"   - 토큰 ID: {stored_token.id}")
                print(f"   - 사용자 UUID: {stored_token.user_uuid}")
                print(f"   - 무효화됨: {stored_token.is_revoked}")
                print(f"   - 만료일: {stored_token.expires_at}")
                print(f"   - 생성일: {stored_token.created_at}")
                
                # 만료 여부 확인
                current_time = datetime.now(timezone.utc)
                if stored_token.expires_at > current_time:
                    print("✅ 토큰이 아직 유효합니다")
                else:
                    print("❌ 토큰이 만료되었습니다")
                
                # 무효화 여부 확인
                if not stored_token.is_revoked:
                    print("✅ 토큰이 무효화되지 않았습니다")
                    print("\n🎉 리프레시 토큰 저장 확인 테스트 성공!")
                else:
                    print("❌ 토큰이 무효화되었습니다")
                    
            else:
                print("❌ 데이터베이스에서 토큰을 찾을 수 없습니다")
                
                # 모든 토큰 조회해서 비교
                all_tokens = db.query(RefreshToken).all()
                print(f"\n📋 전체 토큰 수: {len(all_tokens)}")
                
                for i, token in enumerate(all_tokens[-5:], 1):  # 최근 5개만 확인
                    print(f"   {i}. ID: {token.id}")
                    print(f"      토큰: {token.token[:50]}...")
                    print(f"      무효화됨: {token.is_revoked}")
                    print(f"      생성일: {token.created_at}")
                    
                    # 토큰 비교
                    if token.token == refresh_token:
                        print(f"      ✅ 이 토큰이 일치합니다!")
                        break
                else:
                    print("❌ 일치하는 토큰이 없습니다")
                    
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🔍 리프레시 토큰 저장 확인 테스트 완료")

if __name__ == "__main__":
    test_refresh_token_storage()