#!/usr/bin/env python3
"""
리프레시 토큰 저장 문제 디버깅 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.mail import get_db
from app.model.user_model import User, RefreshToken
from app.service.auth_service import AuthService
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import json

def debug_refresh_token_storage():
    """리프레시 토큰 저장 문제를 디버깅합니다."""
    
    print("🔍 리프레시 토큰 저장 디버깅 시작")
    print("=" * 60)
    
    # 데이터베이스 연결
    db: Session = next(get_db())
    
    try:
        # 1. 관리자 계정 확인
        admin_user = db.query(User).filter(User.email == "admin@skyboot.com").first()
        if not admin_user:
            print("❌ 관리자 계정을 찾을 수 없습니다.")
            return
        
        print(f"✅ 관리자 계정 확인:")
        print(f"   - ID: {admin_user.user_id}")
        print(f"   - UUID: {admin_user.user_uuid}")
        print(f"   - Email: {admin_user.email}")
        print(f"   - 조직 ID: {admin_user.org_id}")
        print()
        
        # 2. 기존 리프레시 토큰 확인
        existing_tokens = db.query(RefreshToken).filter(
            RefreshToken.user_uuid == admin_user.user_uuid
        ).all()
        
        print(f"📋 기존 리프레시 토큰 수: {len(existing_tokens)}")
        for i, token in enumerate(existing_tokens, 1):
            print(f"   {i}. ID: {token.id}")
            print(f"      토큰: {token.token[:50]}...")
            print(f"      만료일: {token.expires_at}")
            print(f"      무효화됨: {token.is_revoked}")
            print(f"      생성일: {token.created_at}")
            print()
        
        # 3. 새 로그인 시뮬레이션
        print("🔄 새 로그인 시뮬레이션 시작")
        
        # AuthService 인스턴스 생성
        auth_service = AuthService(db)
        
        # 사용자 인증
        authenticated_user = auth_service.authenticate_user("admin@skyboot.com", "Admin123!@#")
        
        if authenticated_user:
            print("✅ 사용자 인증 성공")
            
            # 토큰 생성
            login_result = auth_service.create_tokens(authenticated_user)
            print(f"   - 액세스 토큰: {login_result['access_token'][:50]}...")
            print(f"   - 리프레시 토큰: {login_result['refresh_token'][:50]}...")
            
            # 4. 새로 생성된 리프레시 토큰 확인
            new_tokens = db.query(RefreshToken).filter(
                RefreshToken.user_uuid == admin_user.user_uuid,
                RefreshToken.is_revoked == False
            ).all()
            
            print(f"\n📋 로그인 후 활성 리프레시 토큰 수: {len(new_tokens)}")
            for i, token in enumerate(new_tokens, 1):
                print(f"   {i}. ID: {token.id}")
                print(f"      토큰: {token.token[:50]}...")
                print(f"      만료일: {token.expires_at}")
                print(f"      무효화됨: {token.is_revoked}")
                print(f"      생성일: {token.created_at}")
                
                # 토큰이 실제로 저장된 토큰과 일치하는지 확인
                if token.token == login_result['refresh_token']:
                    print(f"      ✅ 이 토큰이 방금 생성된 토큰입니다!")
                print()
            
            # 5. 토큰 검증 테스트
            print("🔍 토큰 검증 테스트")
            refresh_token = login_result['refresh_token']
            
            # JWT 토큰 디코딩 테스트
            try:
                payload = AuthService.verify_token(refresh_token, "refresh")
                if payload:
                    print("✅ JWT 토큰 검증 성공")
                    print(f"   - Subject: {payload.get('sub')}")
                    print(f"   - 조직 ID: {payload.get('org_id')}")
                    print(f"   - 만료일: {payload.get('exp')}")
                    print(f"   - 토큰 타입: {payload.get('type')}")
                else:
                    print("❌ JWT 토큰 검증 실패")
            except Exception as e:
                print(f"❌ JWT 토큰 검증 오류: {str(e)}")
            
            # 6. 데이터베이스에서 토큰 조회 테스트
            print("\n🔍 데이터베이스 토큰 조회 테스트")
            stored_token = db.query(RefreshToken).filter(
                RefreshToken.token == refresh_token
            ).first()
            
            if stored_token:
                print("✅ 데이터베이스에서 토큰 발견")
                print(f"   - 토큰 ID: {stored_token.id}")
                print(f"   - 사용자 UUID: {stored_token.user_uuid}")
                print(f"   - 무효화됨: {stored_token.is_revoked}")
                print(f"   - 만료일: {stored_token.expires_at}")
                print(f"   - 현재 시간: {datetime.now(timezone.utc)}")
                
                # 만료 여부 확인
                if stored_token.expires_at > datetime.now(timezone.utc):
                    print("✅ 토큰이 아직 유효합니다")
                else:
                    print("❌ 토큰이 만료되었습니다")
                    
            else:
                print("❌ 데이터베이스에서 토큰을 찾을 수 없습니다")
                
                # 모든 토큰 다시 조회해서 비교
                all_tokens = db.query(RefreshToken).all()
                print(f"\n전체 토큰 수: {len(all_tokens)}")
                for token in all_tokens:
                    if token.token == refresh_token:
                        print(f"✅ 토큰 발견! ID: {token.id}")
                        break
                else:
                    print("❌ 전체 토큰 중에서도 일치하는 토큰이 없습니다")
        
        else:
            print("❌ 사용자 인증 실패")
            
    except Exception as e:
        print(f"❌ 디버깅 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()
        
    print("\n" + "=" * 60)
    print("🔍 리프레시 토큰 저장 디버깅 완료")

if __name__ == "__main__":
    debug_refresh_token_storage()