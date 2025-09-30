#!/usr/bin/env python3
"""
PostgreSQL 연결 테스트 스크립트
"""

import sys
import os
from sqlalchemy import create_engine, text

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_postgresql_connection():
    """PostgreSQL 연결 테스트"""
    try:
        # 다양한 인코딩 옵션으로 테스트
        connection_configs = [
            {
                "name": "기본 연결",
                "url": "postgresql://skyboot_user:skyboot_password@localhost:5432/skyboot_mail"
            },
            {
                "name": "UTF-8 인코딩 설정",
                "url": "postgresql://skyboot_user:skyboot_password@localhost:5432/skyboot_mail",
                "connect_args": {"client_encoding": "utf8"}
            },
            {
                "name": "UTF-8 + 타임존 설정",
                "url": "postgresql://skyboot_user:skyboot_password@localhost:5432/skyboot_mail",
                "connect_args": {
                    "client_encoding": "utf8",
                    "options": "-c timezone=UTC"
                }
            }
        ]
        
        for config in connection_configs:
            print(f"\n🔧 {config['name']} 테스트 중...")
            
            try:
                if "connect_args" in config:
                    engine = create_engine(config["url"], connect_args=config["connect_args"])
                else:
                    engine = create_engine(config["url"])
                
                # 연결 테스트
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT version()"))
                    version = result.fetchone()[0]
                    print(f"✅ 연결 성공: {version[:50]}...")
                    
                    # 인코딩 확인
                    result = conn.execute(text("SHOW server_encoding"))
                    encoding = result.fetchone()[0]
                    print(f"📝 서버 인코딩: {encoding}")
                    
                    result = conn.execute(text("SHOW client_encoding"))
                    client_encoding = result.fetchone()[0]
                    print(f"📝 클라이언트 인코딩: {client_encoding}")
                    
                    # 한글 테스트
                    result = conn.execute(text("SELECT '테스트 한글' as test_korean"))
                    korean_test = result.fetchone()[0]
                    print(f"🇰🇷 한글 테스트: {korean_test}")
                    
                    print(f"✅ {config['name']} 성공!")
                    return True
                    
            except Exception as e:
                print(f"❌ {config['name']} 실패: {e}")
                continue
        
        print("\n❌ 모든 연결 시도가 실패했습니다.")
        return False
        
    except Exception as e:
        print(f"❌ 연결 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    print("🚀 PostgreSQL 연결 테스트 시작")
    success = test_postgresql_connection()
    
    if success:
        print("\n✅ PostgreSQL 연결 테스트 완료!")
    else:
        print("\n❌ PostgreSQL 연결 테스트 실패!")
        sys.exit(1)