#!/usr/bin/env python3
"""
parent_id 저장 문제 진단 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import settings

def check_parent_id_issue():
    """parent_id 저장 문제를 진단합니다."""
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        print("🔍 parent_id 저장 문제 진단 시작")
        print("=" * 60)
        
        # 1. 최근 생성된 폴더 확인
        print("\n📁 최근 생성된 폴더 데이터:")
        result = conn.execute(text("""
            SELECT id, name, folder_type, parent_id, user_uuid, created_at
            FROM mail_folders 
            ORDER BY created_at DESC 
            LIMIT 10
        """))
        
        folders = result.fetchall()
        for folder in folders:
            print(f"  ID: {folder.id}, 이름: {folder.name}, 타입: {folder.folder_type}")
            print(f"  parent_id: {folder.parent_id}, user_uuid: {folder.user_uuid}")
            print(f"  생성시간: {folder.created_at}")
            print("  " + "-" * 50)
        
        # 2. "업무 메일" 폴더 검색
        print("\n🔍 '업무 메일' 폴더 검색:")
        result = conn.execute(text("""
            SELECT id, name, folder_type, parent_id, user_uuid, created_at
            FROM mail_folders 
            WHERE name = '업무 메일'
            ORDER BY created_at DESC
        """))
        
        work_folders = result.fetchall()
        if work_folders:
            for folder in work_folders:
                print(f"  ID: {folder.id}, 이름: {folder.name}")
                print(f"  parent_id: {folder.parent_id} (예상값: 177)")
                print(f"  user_uuid: {folder.user_uuid}")
                print(f"  생성시간: {folder.created_at}")
        else:
            print("  '업무 메일' 폴더를 찾을 수 없습니다.")
        
        # 3. parent_id가 177인 폴더 확인
        print(f"\n🔍 parent_id가 177인 폴더 확인:")
        result = conn.execute(text("""
            SELECT id, name, folder_type, parent_id, user_uuid
            FROM mail_folders 
            WHERE parent_id = 177
        """))
        
        child_folders = result.fetchall()
        if child_folders:
            for folder in child_folders:
                print(f"  ID: {folder.id}, 이름: {folder.name}, parent_id: {folder.parent_id}")
        else:
            print("  parent_id가 177인 폴더가 없습니다.")
        
        # 4. ID가 177인 폴더 확인 (부모 폴더 존재 여부)
        print(f"\n🔍 ID가 177인 폴더 확인 (부모 폴더 존재 여부):")
        result = conn.execute(text("""
            SELECT id, name, folder_type, parent_id, user_uuid
            FROM mail_folders 
            WHERE id = 177
        """))
        
        parent_folder = result.fetchone()
        if parent_folder:
            print(f"  부모 폴더 존재: ID {parent_folder.id}, 이름: {parent_folder.name}")
        else:
            print("  ❌ ID가 177인 폴더가 존재하지 않습니다!")
            print("  이것이 parent_id 저장 실패의 원인일 수 있습니다.")
        
        # 5. mail_folders 테이블 구조 확인
        print(f"\n📋 mail_folders 테이블 구조:")
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'mail_folders'
            ORDER BY ordinal_position
        """))
        
        columns = result.fetchall()
        for col in columns:
            print(f"  {col.column_name}: {col.data_type} (nullable: {col.is_nullable})")

if __name__ == "__main__":
    check_parent_id_issue()