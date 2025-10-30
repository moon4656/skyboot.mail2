#!/usr/bin/env python3
"""
데이터베이스 외래 키 관계 분석 스크립트
"""

import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.mail import get_db
from sqlalchemy import text

def analyze_foreign_keys():
    """외래 키 관계를 분석합니다."""
    try:
        # 데이터베이스 연결
        db = next(get_db())
        
        print("🔍 외래 키 관계 분석 시작")
        print("=" * 80)
        
        # 확인할 테이블들
        tables_to_check = ['mail_folders', 'mail_users', 'users']
        
        # 1. mail_folders 테이블의 외래 키 관계 확인
        print("\n📋 mail_folders 테이블의 외래 키 관계:")
        result = db.execute(text("""
            SELECT 
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.delete_rule,
                rc.update_rule
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
                JOIN information_schema.referential_constraints AS rc
                  ON tc.constraint_name = rc.constraint_name
            WHERE 
                tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name = 'mail_folders'
            ORDER BY tc.constraint_name;
        """))
        
        fk_results = result.fetchall()
        for row in fk_results:
            print(f"  - {row.column_name} -> {row.foreign_table_name}.{row.foreign_column_name}")
            print(f"    DELETE: {row.delete_rule}, UPDATE: {row.update_rule}")
        
        # 2. mail_users 테이블의 외래 키 관계 확인
        print("\n📋 mail_users 테이블의 외래 키 관계:")
        result = db.execute(text("""
            SELECT 
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.delete_rule,
                rc.update_rule
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
                JOIN information_schema.referential_constraints AS rc
                  ON tc.constraint_name = rc.constraint_name
            WHERE 
                tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name = 'mail_users'
            ORDER BY tc.constraint_name;
        """))
        
        fk_results = result.fetchall()
        for row in fk_results:
            print(f"  - {row.column_name} -> {row.foreign_table_name}.{row.foreign_column_name}")
            print(f"    DELETE: {row.delete_rule}, UPDATE: {row.update_rule}")
        
        # 3. users 테이블의 외래 키 관계 확인
        print("\n📋 users 테이블의 외래 키 관계:")
        result = db.execute(text("""
            SELECT 
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.delete_rule,
                rc.update_rule
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
                JOIN information_schema.referential_constraints AS rc
                  ON tc.constraint_name = rc.constraint_name
            WHERE 
                tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name = 'users'
            ORDER BY tc.constraint_name;
        """))
        
        fk_results = result.fetchall()
        for row in fk_results:
            print(f"  - {row.column_name} -> {row.foreign_table_name}.{row.foreign_column_name}")
            print(f"    DELETE: {row.delete_rule}, UPDATE: {row.update_rule}")
        
        # 4. mail_folders 테이블에서 user_uuid가 참조하는 테이블 확인
        print("\n📋 mail_folders.user_uuid가 참조하는 관계:")
        result = db.execute(text("""
            SELECT 
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.delete_rule,
                rc.update_rule
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                JOIN information_schema.referential_constraints AS rc
                  ON tc.constraint_name = rc.constraint_name
            WHERE 
                tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name = 'mail_folders'
                AND kcu.column_name = 'user_uuid';
        """))
        
        fk_result = result.fetchone()
        if fk_result:
            print(f"  - user_uuid -> {fk_result.foreign_table_name}.{fk_result.foreign_column_name}")
            print(f"    DELETE: {fk_result.delete_rule}, UPDATE: {fk_result.update_rule}")
        else:
            print("  - user_uuid에 대한 외래 키 제약 조건이 없습니다!")
        
        # 5. 현재 데이터 상태 확인
        print("\n📊 현재 데이터 상태:")
        
        # 조직 수
        org_count = db.execute(text("SELECT COUNT(*) FROM organizations")).fetchone()[0]
        print(f"   - 조직 수: {org_count}")
        
        # 사용자 수
        user_count = db.execute(text("SELECT COUNT(*) FROM users")).fetchone()[0]
        print(f"   - 사용자 수: {user_count}")
        
        # 메일 사용자 수
        mail_user_count = db.execute(text("SELECT COUNT(*) FROM mail_users")).fetchone()[0]
        print(f"   - 메일 사용자 수: {mail_user_count}")
        
        # 메일 폴더 수
        mail_folder_count = db.execute(text("SELECT COUNT(*) FROM mail_folders")).fetchone()[0]
        print(f"   - 메일 폴더 수: {mail_folder_count}")
        
        # NULL user_uuid를 가진 mail_folders 확인
        null_user_uuid_count = db.execute(text("SELECT COUNT(*) FROM mail_folders WHERE user_uuid IS NULL")).fetchone()[0]
        print(f"   - NULL user_uuid를 가진 mail_folders: {null_user_uuid_count}")
        
        # NULL org_id를 가진 mail_users 확인
        null_org_id_count = db.execute(text("SELECT COUNT(*) FROM mail_users WHERE org_id IS NULL")).fetchone()[0]
        print(f"   - NULL org_id를 가진 mail_users: {null_org_id_count}")
        
        if null_user_uuid_count > 0:
            print("\n⚠️ user_uuid가 NULL인 메일 폴더들:")
            result = db.execute(text("""
                SELECT id, folder_uuid, name, org_id, user_uuid 
                FROM mail_folders 
                WHERE user_uuid IS NULL 
                LIMIT 10
            """))
            null_folders = result.fetchall()
            for folder in null_folders:
                print(f"    - ID: {folder.id}, UUID: {folder.folder_uuid}, "
                      f"이름: {folder.name}, 조직: {folder.org_id}")
        
        db.close()
        print("\n✅ 외래 키 관계 분석 완료")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_foreign_keys()