#!/usr/bin/env python3
"""
JWT 토큰 디코딩 스크립트
"""

import jwt
import json
from datetime import datetime

def decode_jwt_token(token):
    """JWT 토큰을 디코딩하여 정보를 출력합니다."""
    print("🔐 JWT 토큰 정보 분석")
    print("=" * 60)
    
    try:
        # JWT 토큰을 검증 없이 디코딩 (정보 확인용)
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        print("📋 토큰 페이로드 정보:")
        print("-" * 40)
        
        # 사용자 정보
        print(f"🆔 사용자 ID (sub): {decoded.get('sub', 'N/A')}")
        print(f"📧 이메일: {decoded.get('email', 'N/A')}")
        print(f"👤 사용자명: {decoded.get('username', 'N/A')}")
        print(f"🔑 관리자 여부: {'예' if decoded.get('is_admin', False) else '아니오'}")
        print(f"👥 역할: {decoded.get('role', 'N/A')}")
        
        print("\n🏢 조직 정보:")
        print("-" * 40)
        print(f"🆔 조직 ID: {decoded.get('org_id', 'N/A')}")
        print(f"🏢 조직명: {decoded.get('org_name', 'N/A')}")
        print(f"🌐 조직 도메인: {decoded.get('org_domain', 'N/A')}")
        
        print("\n⏰ 토큰 정보:")
        print("-" * 40)
        
        # 만료 시간 처리
        exp_timestamp = decoded.get('exp')
        if exp_timestamp:
            exp_datetime = datetime.fromtimestamp(exp_timestamp)
            current_time = datetime.now()
            is_expired = current_time > exp_datetime
            
            print(f"⏰ 만료 시간: {exp_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🕐 현재 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"✅ 토큰 상태: {'만료됨' if is_expired else '유효함'}")
            
            if not is_expired:
                time_left = exp_datetime - current_time
                hours_left = int(time_left.total_seconds() // 3600)
                minutes_left = int((time_left.total_seconds() % 3600) // 60)
                print(f"⏳ 남은 시간: {hours_left}시간 {minutes_left}분")
        else:
            print("⏰ 만료 시간: 정보 없음")
        
        print(f"🎫 토큰 타입: {decoded.get('type', 'N/A')}")
        print(f"🆔 JWT ID (jti): {decoded.get('jti', 'N/A')}")
        
        print("\n📄 전체 페이로드 (JSON):")
        print("-" * 40)
        print(json.dumps(decoded, indent=2, ensure_ascii=False))
        
        return decoded
        
    except jwt.InvalidTokenError as e:
        print(f"❌ JWT 토큰 디코딩 오류: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {str(e)}")
        return None

def main():
    # 제공된 JWT 토큰
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzYjk1OTIxOS1kYTEwLTQyYmItOTY5My0wYWEzZWQ1MDJjZDMiLCJlbWFpbCI6InVzZXIwMUBleGFtcGxlLmNvbSIsInVzZXJuYW1lIjoiXHVjNzc0XHVjMTMxXHVjNmE5IiwiaXNfYWRtaW4iOmZhbHNlLCJyb2xlIjoidXNlciIsIm9yZ19pZCI6IjM4NTZhOGMxLTg0YTQtNDAxOS05MTMzLTY1NWNhY2FiNGJjOSIsIm9yZ19uYW1lIjoiXHVhZTMwXHViY2Y4IFx1Yzg3MFx1YzljMSIsIm9yZ19kb21haW4iOiJsb2NhbGhvc3QiLCJleHAiOjE3NTk3NTMxMDIsInR5cGUiOiJhY2Nlc3MiLCJqdGkiOiI3NzM5MDUyYy0yYmI0LTQ4ODMtODA4MS1hYzkwZjgyOGFiYTkifQ.fGtT6HzcKVNlg7rJg3Fi8NNZ1E4ej64k_3tAYm7XUXU"
    
    decode_jwt_token(token)

if __name__ == "__main__":
    main()