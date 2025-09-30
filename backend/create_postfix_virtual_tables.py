#!/usr/bin/env python3
"""
Postfix 가상 테이블 생성 및 데이터 동기화 스크립트
"""
import psycopg2

def create_postfix_virtual_tables():
    try:
        conn = psycopg2.connect(
            host='172.18.0.1',
            database='skybootmail',
            user='postgres',
            password='safe70!!'
        )
        cur = conn.cursor()
        
        print('🔧 Postfix 가상 테이블 생성 중...')
        
        # 먼저 테이블 구조 확인
        print('📋 기존 테이블 구조 확인...')
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position;
        """)
        user_columns = cur.fetchall()
        print('users 테이블 컬럼:', [col[0] for col in user_columns])
        
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'organizations' 
            ORDER BY ordinal_position;
        """)
        org_columns = cur.fetchall()
        print('organizations 테이블 컬럼:', [col[0] for col in org_columns])
        
        # 1. virtual_domains 테이블 생성
        print('📋 virtual_domains 테이블 생성...')
        cur.execute("""
            CREATE TABLE IF NOT EXISTS virtual_domains (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 2. virtual_users 테이블 생성
        print('👤 virtual_users 테이블 생성...')
        cur.execute("""
            CREATE TABLE IF NOT EXISTS virtual_users (
                id SERIAL PRIMARY KEY,
                domain_id INTEGER REFERENCES virtual_domains(id),
                email VARCHAR(255) NOT NULL UNIQUE,
                password VARCHAR(255),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 3. virtual_aliases 테이블 생성
        print('📧 virtual_aliases 테이블 생성...')
        cur.execute("""
            CREATE TABLE IF NOT EXISTS virtual_aliases (
                id SERIAL PRIMARY KEY,
                domain_id INTEGER REFERENCES virtual_domains(id),
                source VARCHAR(255) NOT NULL,
                destination VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 4. 기존 조직 데이터에서 도메인 추출 및 삽입
        print('🏢 조직 도메인 데이터 동기화...')
        cur.execute("""
            INSERT INTO virtual_domains (name, is_active)
            SELECT DISTINCT domain, is_active 
            FROM organizations 
            WHERE domain IS NOT NULL 
            ON CONFLICT (name) DO NOTHING;
        """)
        
        # 5. 기본 도메인 추가 (localhost)
        print('🏠 기본 도메인 추가...')
        cur.execute("""
            INSERT INTO virtual_domains (name, is_active)
            VALUES ('localhost', TRUE)
            ON CONFLICT (name) DO NOTHING;
        """)
        
        # 6. 외부 메일 사용자 추가 (mail_users 테이블에서)
        print('📮 메일 사용자 동기화...')
        cur.execute("""
            INSERT INTO virtual_users (email, is_active)
            SELECT DISTINCT 
                mu.email,
                TRUE
            FROM mail_users mu
            WHERE mu.email IS NOT NULL
            ON CONFLICT (email) DO NOTHING;
        """)
        
        # 7. 기존 사용자 데이터 동기화 (컬럼명 확인 후)
        print('👥 사용자 데이터 동기화...')
        # 먼저 users 테이블에 org_uuid 컬럼이 있는지 확인
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name IN ('org_uuid', 'organization_id');
        """)
        org_column = cur.fetchone()
        
        if org_column:
            org_col_name = org_column[0]
            print(f'조직 연결 컬럼: {org_col_name}')
            
            if org_col_name == 'org_uuid':
                cur.execute("""
                    INSERT INTO virtual_users (domain_id, email, is_active)
                    SELECT 
                        vd.id as domain_id,
                        u.email,
                        u.is_active
                    FROM users u
                    JOIN organizations o ON u.org_uuid = o.org_uuid
                    JOIN virtual_domains vd ON o.domain = vd.name
                    WHERE u.email IS NOT NULL
                    ON CONFLICT (email) DO NOTHING;
                """)
            else:
                cur.execute("""
                    INSERT INTO virtual_users (domain_id, email, is_active)
                    SELECT 
                        vd.id as domain_id,
                        u.email,
                        u.is_active
                    FROM users u
                    JOIN organizations o ON u.organization_id = o.id
                    JOIN virtual_domains vd ON o.domain = vd.name
                    WHERE u.email IS NOT NULL
                    ON CONFLICT (email) DO NOTHING;
                """)
        else:
            print('조직 연결 컬럼을 찾을 수 없음, 사용자만 추가')
            cur.execute("""
                INSERT INTO virtual_users (email, is_active)
                SELECT DISTINCT email, is_active
                FROM users
                WHERE email IS NOT NULL
                ON CONFLICT (email) DO NOTHING;
            """)
        
        conn.commit()
        
        # 8. 결과 확인
        print('\n📊 생성된 테이블 확인:')
        
        cur.execute('SELECT COUNT(*) FROM virtual_domains;')
        domains_count = cur.fetchone()[0]
        print(f'virtual_domains: {domains_count}개')
        
        cur.execute('SELECT COUNT(*) FROM virtual_users;')
        users_count = cur.fetchone()[0]
        print(f'virtual_users: {users_count}개')
        
        cur.execute('SELECT COUNT(*) FROM virtual_aliases;')
        aliases_count = cur.fetchone()[0]
        print(f'virtual_aliases: {aliases_count}개')
        
        # 9. 도메인 목록 출력
        print('\n🌐 등록된 도메인:')
        cur.execute('SELECT name FROM virtual_domains ORDER BY name;')
        domains = cur.fetchall()
        for domain in domains:
            print(f'  - {domain[0]}')
        
        # 10. 사용자 샘플 출력
        print('\n👤 등록된 사용자 (처음 10개):')
        cur.execute('SELECT email FROM virtual_users ORDER BY email LIMIT 10;')
        users = cur.fetchall()
        for user in users:
            print(f'  - {user[0]}')
        
        conn.close()
        print('\n✅ Postfix 가상 테이블 생성 및 동기화 완료!')
        
    except Exception as e:
        print(f'❌ 오류 발생: {e}')
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    create_postfix_virtual_tables()