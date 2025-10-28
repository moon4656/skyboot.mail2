#!/usr/bin/env python3
"""
SkyBoot Mail SaaS - Addressbook 테이블 생성 스크립트
다중 조직 지원 및 데이터 격리를 위한 addressbook 테이블들을 생성합니다.
"""

import psycopg2
from app.config import settings

def create_addressbook_tables():
    """addressbook 관련 테이블들을 생성합니다."""
    
    # SQL 스크립트
    sql_script = """
    -- 1. departments 테이블 생성
    CREATE TABLE IF NOT EXISTS departments (
        id SERIAL PRIMARY KEY,
        org_id VARCHAR(36) NOT NULL REFERENCES organizations(org_id),
        name VARCHAR(100) NOT NULL,
        parent_id INTEGER REFERENCES departments(id),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE,
        CONSTRAINT unique_org_department_name UNIQUE (org_id, name)
    );

    -- 2. groups 테이블 생성
    CREATE TABLE IF NOT EXISTS groups (
        id SERIAL PRIMARY KEY,
        org_id VARCHAR(36) NOT NULL REFERENCES organizations(org_id),
        name VARCHAR(100) NOT NULL,
        description TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE,
        CONSTRAINT unique_org_group_name UNIQUE (org_id, name)
    );

    -- 3. contacts 테이블 생성
    CREATE TABLE IF NOT EXISTS contacts (
        contact_uuid VARCHAR(36) PRIMARY KEY,
        org_id VARCHAR(36) NOT NULL REFERENCES organizations(org_id),
        name VARCHAR(100) NOT NULL,
        email VARCHAR(255),
        phone VARCHAR(50),
        mobile VARCHAR(50),
        company VARCHAR(200),
        title VARCHAR(100),
        department_id INTEGER REFERENCES departments(id),
        address TEXT,
        memo TEXT,
        favorite BOOLEAN DEFAULT FALSE,
        profile_image_url VARCHAR(500),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE,
        CONSTRAINT unique_org_contact_email UNIQUE (org_id, email)
    );

    -- 4. contact_groups 테이블 생성 (다대다 관계)
    CREATE TABLE IF NOT EXISTS contact_groups (
        id SERIAL PRIMARY KEY,
        org_id VARCHAR(36) NOT NULL REFERENCES organizations(org_id),
        contact_uuid VARCHAR(36) NOT NULL REFERENCES contacts(contact_uuid),
        group_id INTEGER NOT NULL REFERENCES groups(id),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT unique_org_contact_group UNIQUE (org_id, contact_uuid, group_id)
    );

    -- 인덱스 생성 (성능 최적화)
    CREATE INDEX IF NOT EXISTS idx_departments_org_id ON departments(org_id);
    CREATE INDEX IF NOT EXISTS idx_groups_org_id ON groups(org_id);
    CREATE INDEX IF NOT EXISTS idx_contacts_org_id ON contacts(org_id);
    CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
    CREATE INDEX IF NOT EXISTS idx_contact_groups_org_id ON contact_groups(org_id);
    CREATE INDEX IF NOT EXISTS idx_contact_groups_contact_uuid ON contact_groups(contact_uuid);
    CREATE INDEX IF NOT EXISTS idx_contact_groups_group_id ON contact_groups(group_id);
    """
    
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        cursor = conn.cursor()
        
        print('🚀 Addressbook 테이블 생성을 시작합니다...')
        
        # SQL 스크립트 실행
        cursor.execute(sql_script)
        conn.commit()
        
        print('✅ Addressbook 테이블들이 성공적으로 생성되었습니다!')
        
        # 생성된 테이블 확인
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('contacts', 'departments', 'groups', 'contact_groups')
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print('\n📋 생성된 addressbook 테이블 목록:')
        for table in tables:
            print(f'   ✅ {table[0]}')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'❌ 테이블 생성 중 오류 발생: {e}')
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    create_addressbook_tables()