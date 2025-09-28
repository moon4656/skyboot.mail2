#!/usr/bin/env python3
"""
Organization 테이블의 구조와 데이터를 확인합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.config import settings

def check_table_structure():
    """테이블 구조와 데이터를 확인합니다."""
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            print("🔍 Organizations 테이블 구조 확인...")
            
            # 테이블 구조 확인
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'organizations' 
                ORDER BY ordinal_position;
            """))
            
            print("\n📋 Organizations 테이블 구조:")
            for row in result:
                print(f"  {row.column_name}: {row.data_type} (nullable: {row.is_nullable}, default: {row.column_default})")
            
            # 데이터 개수 확인
            result = conn.execute(text("SELECT COUNT(*) as count FROM organizations"))
            count = result.fetchone().count
            print(f"\n📊 Organizations 테이블 데이터 개수: {count}")
            
            if count > 0:
                # 샘플 데이터 확인 (features 컬럼 제외)
                result = conn.execute(text("""
                    SELECT org_id, org_code, display_name, subdomain, admin_email
                    FROM organizations 
                    LIMIT 3;
                """))
                
                print("\n📋 샘플 데이터:")
                for row in result:
                    print(f"  org_id: {row.org_id}, org_code: {row.org_code}, display_name: {row.display_name}")
            
            # organization_settings 테이블 구조 확인
            print("\n🔍 Organization_settings 테이블 구조 확인...")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'organization_settings' 
                ORDER BY ordinal_position;
            """))
            
            print("\n📋 Organization_settings 테이블 구조:")
            for row in result:
                print(f"  {row.column_name}: {row.data_type} (nullable: {row.is_nullable}, default: {row.column_default})")
            
            # organization_usage 테이블 구조 확인
            print("\n🔍 Organization_usage 테이블 구조 확인...")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'organization_usage' 
                ORDER BY ordinal_position;
            """))
            
            print("\n📋 Organization_usage 테이블 구조:")
            for row in result:
                print(f"  {row.column_name}: {row.data_type} (nullable: {row.is_nullable}, default: {row.column_default})")
            
    except Exception as e:
        print(f"❌ 테이블 구조 확인 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    check_table_structure()