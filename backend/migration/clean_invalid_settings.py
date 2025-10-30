#!/usr/bin/env python3
"""
허용되지 않은 조직 설정 키를 데이터베이스에서 제거하는 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import settings

def clean_invalid_settings():
    """허용되지 않은 설정 키들을 데이터베이스에서 제거합니다."""
    
    # 허용된 설정 키들 (OrganizationBase.validate_settings와 동일)
    allowed_keys = {
        'feature_flags', 'features', 'theme', 'power', 
        'imap_enabled', 'smtp_enabled', 'mail_server_enabled'
    }
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            print("🔍 현재 organization_settings 테이블의 설정 키 확인...")
            
            # 현재 존재하는 모든 설정 키 조회
            result = conn.execute(text("""
                SELECT DISTINCT setting_key, COUNT(*) as count
                FROM organization_settings 
                GROUP BY setting_key
                ORDER BY setting_key;
            """))
            
            all_keys = result.fetchall()
            print("\n📋 현재 데이터베이스의 설정 키들:")
            invalid_keys = []
            
            for row in all_keys:
                key, count = row
                status = "✅ 허용됨" if key in allowed_keys else "❌ 허용되지 않음"
                print(f"  - {key}: {count}개 ({status})")
                
                if key not in allowed_keys:
                    invalid_keys.append(key)
            
            if not invalid_keys:
                print("\n✅ 허용되지 않은 설정 키가 없습니다.")
                return
            
            print(f"\n🗑️ 제거할 허용되지 않은 설정 키들: {invalid_keys}")
            print("⚠️ 자동으로 삭제를 진행합니다...")
            
            # 허용되지 않은 설정 키들 삭제
            total_deleted = 0
            for key in invalid_keys:
                result = conn.execute(text("""
                    DELETE FROM organization_settings 
                    WHERE setting_key = :key
                """), {"key": key})
                
                deleted_count = result.rowcount
                total_deleted += deleted_count
                print(f"🗑️ '{key}' 키 삭제 완료: {deleted_count}개 레코드")
            
            # 변경사항 커밋
            conn.commit()
            print(f"\n✅ 허용되지 않은 설정 키 제거 완료! (총 {total_deleted}개 레코드 삭제)")
            
            # 결과 확인
            print("\n🔍 제거 후 남은 설정 키들:")
            result = conn.execute(text("""
                SELECT DISTINCT setting_key, COUNT(*) as count
                FROM organization_settings 
                GROUP BY setting_key
                ORDER BY setting_key;
            """))
            
            remaining_keys = result.fetchall()
            for row in remaining_keys:
                key, count = row
                print(f"  - {key}: {count}개")
                
    except Exception as e:
        print(f"❌ 데이터베이스 연결 오류: {str(e)}")

if __name__ == "__main__":
    clean_invalid_settings()