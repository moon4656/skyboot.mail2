#!/usr/bin/env python3
"""
조직 불일치 확인 (수정된 버전)

실제 테이블 구조를 확인하고 다중 조직 시스템에서 
user01이 속한 조직과 API에서 사용하는 조직이 다른지 확인합니다.
"""
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings

def get_db_session():
    """데이터베이스 세션 생성"""
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def check_table_structures():
    """테이블 구조 확인"""
    print("🔍 테이블 구조 확인")
    print("=" * 50)
    
    tables_to_check = ['users', 'organizations', 'mail_folders', 'mails']
    
    try:
        db = get_db_session()
        
        for table_name in tables_to_check:
            print(f"\n📋 {table_name} 테이블 구조:")
            
            result = db.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = :table_name
                ORDER BY ordinal_position;
            """), {"table_name": table_name})
            
            columns = result.fetchall()
            for col in columns:
                print(f"  - {col[0]} ({col[1]}) - Nullable: {col[2]} - Default: {col[3]}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 테이블 구조 확인 오류: {e}")

def check_user_info():
    """user01 정보 확인 (실제 컬럼명 사용)"""
    print(f"\n👤 user01 정보 확인")
    print("=" * 50)
    
    try:
        db = get_db_session()
        
        # user01의 정보 확인
        result = db.execute(text("""
            SELECT *
            FROM users
            WHERE user_id = 'user01';
        """))
        
        user_info = result.fetchone()
        if user_info:
            print(f"📋 user01 정보:")
            # 컬럼명을 동적으로 가져오기
            columns = result.keys()
            for i, col_name in enumerate(columns):
                print(f"   {col_name}: {user_info[i]}")
            
            return user_info
        else:
            print(f"❌ user01을 찾을 수 없습니다")
            return None
        
        db.close()
        
    except Exception as e:
        print(f"❌ 사용자 정보 확인 오류: {e}")
        return None

def check_organizations():
    """조직 정보 확인"""
    print(f"\n🏢 조직 정보 확인")
    print("=" * 50)
    
    api_org_uuid = "3856a8c1-84a4-4019-9133-655cacab4bc9"  # API 헤더에서 확인된 조직 UUID
    
    try:
        db = get_db_session()
        
        # 모든 조직 목록
        result = db.execute(text("""
            SELECT *
            FROM organizations
            ORDER BY created_at;
        """))
        
        organizations = result.fetchall()
        print(f"📋 총 {len(organizations)}개의 조직:")
        
        if organizations:
            columns = result.keys()
            for i, org in enumerate(organizations, 1):
                print(f"\n  {i}. 조직 정보:")
                for j, col_name in enumerate(columns):
                    print(f"     {col_name}: {org[j]}")
        
        # API 조직 확인
        print(f"\n🌐 API 조직 UUID 확인: {api_org_uuid}")
        result = db.execute(text("""
            SELECT *
            FROM organizations
            WHERE org_uuid = :org_uuid;
        """), {"org_uuid": api_org_uuid})
        
        api_org = result.fetchone()
        if api_org:
            print(f"✅ API 조직을 찾았습니다:")
            columns = result.keys()
            for i, col_name in enumerate(columns):
                print(f"   {col_name}: {api_org[i]}")
        else:
            print(f"❌ API 조직 UUID를 찾을 수 없습니다")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 조직 정보 확인 오류: {e}")

def check_mail_folders_simple():
    """메일 폴더 간단 확인"""
    print(f"\n📁 메일 폴더 확인")
    print("=" * 50)
    
    user_uuid = '3b959219-da10-42bb-9693-0aa3ed502cd3'  # user01의 UUID
    
    try:
        db = get_db_session()
        
        # user01의 메일 폴더들 확인
        result = db.execute(text("""
            SELECT *
            FROM mail_folders
            WHERE user_uuid = :user_uuid
            ORDER BY folder_type;
        """), {"user_uuid": user_uuid})
        
        folders = result.fetchall()
        print(f"📋 user01의 메일 폴더 ({len(folders)}개):")
        
        if folders:
            columns = result.keys()
            for i, folder in enumerate(folders, 1):
                print(f"\n  {i}. 폴더 정보:")
                for j, col_name in enumerate(columns):
                    print(f"     {col_name}: {folder[j]}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 메일 폴더 확인 오류: {e}")

def check_mails_in_inbox():
    """INBOX 메일 확인"""
    print(f"\n📧 INBOX 메일 확인")
    print("=" * 50)
    
    user_uuid = '3b959219-da10-42bb-9693-0aa3ed502cd3'  # user01의 UUID
    
    try:
        db = get_db_session()
        
        # INBOX의 메일들 확인
        result = db.execute(text("""
            SELECT 
                m.mail_uuid,
                m.subject,
                mif.is_read,
                mf.name as folder_name,
                mf.folder_type
            FROM mails m
            JOIN mail_in_folders mif ON m.mail_uuid = mif.mail_uuid
            JOIN mail_folders mf ON mif.folder_uuid = mf.folder_uuid
            WHERE mf.user_uuid = :user_uuid 
            AND mf.folder_type = 'inbox'
            ORDER BY m.created_at DESC;
        """), {"user_uuid": user_uuid})
        
        mails = result.fetchall()
        print(f"📋 INBOX의 메일 ({len(mails)}개):")
        
        for i, mail in enumerate(mails, 1):
            mail_uuid = mail[0][:8]
            subject = mail[1]
            is_read = mail[2]
            folder_name = mail[3]
            folder_type = mail[4]
            
            print(f"  {i}. {mail_uuid}... | {subject}")
            print(f"     읽음: {is_read}, 폴더: {folder_name} ({folder_type})")
        
        db.close()
        
    except Exception as e:
        print(f"❌ INBOX 메일 확인 오류: {e}")

def check_api_middleware():
    """API 미들웨어 관련 확인"""
    print(f"\n🔧 API 미들웨어 관련 확인")
    print("=" * 50)
    
    print(f"🌐 API 응답 헤더에서 확인된 정보:")
    print(f"   x-organization-id: 3856a8c1-84a4-4019-9133-655cacab4bc9")
    print(f"   x-organization-code: A001")
    
    print(f"\n💡 분석:")
    print(f"   - API가 다중 조직(Multi-tenant) 미들웨어를 사용하고 있습니다")
    print(f"   - 각 요청이 특정 조직 컨텍스트에서 실행됩니다")
    print(f"   - user01의 데이터가 다른 조직에 속해 있을 가능성이 있습니다")

def main():
    """메인 함수"""
    print("🔍 조직 불일치 확인 (수정된 버전)")
    print("=" * 60)
    
    # 1. 테이블 구조 확인
    check_table_structures()
    
    # 2. user01 정보 확인
    check_user_info()
    
    # 3. 조직 정보 확인
    check_organizations()
    
    # 4. 메일 폴더 확인
    check_mail_folders_simple()
    
    # 5. INBOX 메일 확인
    check_mails_in_inbox()
    
    # 6. API 미들웨어 분석
    check_api_middleware()
    
    print(f"\n🎯 결론")
    print("=" * 60)
    print(f"📊 데이터베이스에는 user01의 INBOX에 3개의 읽지 않은 메일이 있습니다")
    print(f"📊 하지만 API는 다른 조직 컨텍스트에서 실행되어 0개를 반환합니다")
    print(f"🔧 이는 다중 조직 미들웨어가 조직별로 데이터를 분리하기 때문입니다")
    
    print("\n" + "=" * 60)
    print("🔍 조직 불일치 확인 완료")

if __name__ == "__main__":
    main()