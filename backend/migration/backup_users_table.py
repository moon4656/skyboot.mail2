#!/usr/bin/env python3
"""
users 테이블 데이터 백업 스크립트
"""

import os
import sys
import json
import psycopg2
from datetime import datetime
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def get_db_connection():
    """데이터베이스 연결을 반환합니다."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "skyboot_mail"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "1234")
        )
        return conn
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return None

def backup_users_table():
    """users 테이블 데이터를 백업합니다."""
    
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            print("📊 users 테이블 데이터 백업을 시작합니다...")
            
            # users 테이블 컬럼 정보 조회
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position
            """)
            columns_info = cursor.fetchall()
            
            print(f"📋 테이블 컬럼 정보:")
            for col in columns_info:
                print(f"   - {col['column_name']} ({col['data_type']})")
            
            # users 테이블 데이터 조회
            cursor.execute("SELECT * FROM users ORDER BY created_at")
            users_data = cursor.fetchall()
            
            # 데이터를 JSON 직렬화 가능한 형태로 변환
            backup_data = []
            for row in users_data:
                row_dict = dict(row)
                # datetime 객체를 문자열로 변환
                for key, value in row_dict.items():
                    if hasattr(value, 'isoformat'):
                        row_dict[key] = value.isoformat()
                    elif value is None:
                        row_dict[key] = None
                    else:
                        row_dict[key] = str(value) if not isinstance(value, (str, int, float, bool)) else value
                backup_data.append(row_dict)
            
            # 백업 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"users_backup_{timestamp}.json"
            backup_path = os.path.join("table_backups", backup_filename)
            
            # 백업 디렉토리 생성
            os.makedirs("table_backups", exist_ok=True)
            
            # 백업 데이터 저장
            backup_info = {
                "table_name": "users",
                "backup_timestamp": timestamp,
                "record_count": len(backup_data),
                "columns_info": [dict(col) for col in columns_info],
                "data": backup_data
            }
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)
            
            print(f"✅ users 테이블 백업 완료!")
            print(f"   - 레코드 수: {len(backup_data)}개")
            print(f"   - 백업 파일: {backup_path}")
            
            # 백업된 데이터 요약 출력
            if backup_data:
                print(f"\n📋 백업된 사용자 정보:")
                for i, user in enumerate(backup_data[:5], 1):  # 처음 5개만 표시
                    username = user.get('username', 'N/A')
                    email = user.get('email', 'N/A')
                    user_id = user.get('user_id', 'N/A')
                    print(f"   {i}. {user_id} - {username} ({email})")
                if len(backup_data) > 5:
                    print(f"   ... 외 {len(backup_data) - 5}개")
            
            return backup_path
        
    except Exception as e:
        print(f"❌ 백업 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    backup_path = backup_users_table()
    if backup_path:
        print(f"\n🎉 백업이 성공적으로 완료되었습니다: {backup_path}")
    else:
        print("\n💥 백업에 실패했습니다.")
        sys.exit(1)