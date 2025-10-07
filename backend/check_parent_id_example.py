#!/usr/bin/env python3
"""
parent_id 필드의 의미를 확인하기 위한 스크립트
폴더 계층 구조 예시를 조회합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.config import settings

def check_parent_id_meaning():
    """parent_id 필드의 의미와 폴더 계층 구조 확인"""
    print("🔍 parent_id 필드 의미 확인")
    print("=" * 60)
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # 1. mail_folders 테이블 구조 확인
            print("\n📋 mail_folders 테이블 구조:")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'mail_folders'
                AND column_name IN ('id', 'parent_id', 'name', 'folder_type')
                ORDER BY ordinal_position;
            """))
            
            for row in result:
                print(f"  - {row[0]} ({row[1]}) - Nullable: {row[2]} - Default: {row[3]}")
            
            # 2. 현재 폴더 데이터 확인
            print("\n📁 현재 폴더 데이터 (계층 구조 포함):")
            result = conn.execute(text("""
                SELECT 
                    f.id,
                    f.name,
                    f.folder_type,
                    f.parent_id,
                    p.name as parent_name,
                    f.user_uuid
                FROM mail_folders f
                LEFT JOIN mail_folders p ON f.parent_id = p.id
                ORDER BY f.user_uuid, f.parent_id NULLS FIRST, f.id
                LIMIT 10;
            """))
            
            folders = result.fetchall()
            if folders:
                print("  ID | 폴더명 | 타입 | 상위폴더ID | 상위폴더명 | 사용자")
                print("  " + "-" * 70)
                for folder in folders:
                    parent_info = f"{folder[3]} ({folder[4]})" if folder[3] else "None (최상위)"
                    print(f"  {folder[0]:2} | {folder[1]:10} | {folder[2]:6} | {parent_info:20} | {folder[5][:8]}...")
            else:
                print("  폴더 데이터가 없습니다.")
            
            # 3. 폴더 계층 구조 예시 생성
            print("\n🌳 폴더 계층 구조 예시:")
            print("  parent_id의 의미:")
            print("  - parent_id = null: 최상위 폴더 (루트 레벨)")
            print("  - parent_id = 1: ID가 1인 폴더의 하위 폴더")
            print("  - parent_id = 2: ID가 2인 폴더의 하위 폴더")
            print()
            print("  예시 구조:")
            print("  📁 받은편지함 (id=1, parent_id=null)")
            print("  📁 보낸편지함 (id=2, parent_id=null)")
            print("  📁 업무 메일 (id=3, parent_id=null)")
            print("    └── 📁 프로젝트 A (id=4, parent_id=3)")
            print("    └── 📁 프로젝트 B (id=5, parent_id=3)")
            print("        └── 📁 회의록 (id=6, parent_id=5)")
            print("  📁 개인 메일 (id=7, parent_id=null)")
            print("    └── 📁 가족 (id=8, parent_id=7)")
            print("    └── 📁 친구 (id=9, parent_id=7)")
            
            # 4. Swagger 예시 설명
            print("\n📝 Swagger 예시 설명:")
            print("  {")
            print('    "name": "프로젝트 A",')
            print('    "folder_type": "custom",')
            print('    "parent_id": 3')
            print("  }")
            print()
            print("  위 예시의 의미:")
            print("  - name: 새로 생성할 폴더의 이름")
            print("  - folder_type: 폴더 타입 (custom = 사용자 정의 폴더)")
            print("  - parent_id: 3 → ID가 3인 '업무 메일' 폴더의 하위 폴더로 생성")
            print()
            print("  만약 parent_id가 null이면:")
            print("  - 최상위 레벨에 폴더가 생성됩니다")
            print("  - 다른 폴더의 하위가 아닌 독립적인 폴더입니다")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    check_parent_id_meaning()