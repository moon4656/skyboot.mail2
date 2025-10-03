"""
직접 SQL을 사용해서 테이블을 생성하는 스크립트
"""
import psycopg2
from datetime import datetime

# 데이터베이스 연결 설정
DB_CONFIG = {
    'host': 'localhost',
    'database': 'skyboot_mail',
    'user': 'postgres',
    'password': 'safe70!!',
    'port': '5432',
    'client_encoding': 'utf8'
}

def create_tables_sql():
    """SQL을 사용해서 직접 테이블을 생성합니다."""
    
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("🚀 SQL을 사용한 테이블 생성 시작")
        print("=" * 60)
        
        # 1. organizations 테이블 생성
        print("📋 1. organizations 테이블 생성...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS organizations (
                org_id VARCHAR(36) PRIMARY KEY,
                org_code VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                subdomain VARCHAR(100) UNIQUE NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                max_users INTEGER DEFAULT 100,
                max_storage_gb INTEGER DEFAULT 10,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✅ organizations 테이블 생성 완료")
        
        # 2. mail_users 테이블 생성
        print("📋 2. mail_users 테이블 생성...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mail_users (
                user_id VARCHAR(50) PRIMARY KEY,
                user_uuid VARCHAR(36) UNIQUE NOT NULL,
                org_id VARCHAR(36) NOT NULL REFERENCES organizations(org_id),
                email VARCHAR(255) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                display_name VARCHAR(100),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✅ mail_users 테이블 생성 완료")
        
        # 3. mails 테이블 생성
        print("📋 3. mails 테이블 생성...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mails (
                mail_uuid VARCHAR(36) PRIMARY KEY,
                sender_uuid VARCHAR(36) NOT NULL,
                org_id VARCHAR(36) NOT NULL REFERENCES organizations(org_id),
                subject VARCHAR(500),
                content TEXT,
                html_content TEXT,
                status VARCHAR(20) DEFAULT 'draft',
                priority VARCHAR(20) DEFAULT 'normal',
                is_read BOOLEAN DEFAULT FALSE,
                is_starred BOOLEAN DEFAULT FALSE,
                is_deleted BOOLEAN DEFAULT FALSE,
                sent_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✅ mails 테이블 생성 완료")
        
        # 4. mail_recipients 테이블 생성
        print("📋 4. mail_recipients 테이블 생성...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mail_recipients (
                id SERIAL PRIMARY KEY,
                mail_uuid VARCHAR(36) NOT NULL REFERENCES mails(mail_uuid),
                recipient_uuid VARCHAR(36),
                recipient_email VARCHAR(255) NOT NULL,
                recipient_type VARCHAR(10) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✅ mail_recipients 테이블 생성 완료")
        
        # 5. mail_attachments 테이블 생성
        print("📋 5. mail_attachments 테이블 생성...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mail_attachments (
                id SERIAL PRIMARY KEY,
                mail_uuid VARCHAR(36) NOT NULL REFERENCES mails(mail_uuid),
                filename VARCHAR(255) NOT NULL,
                original_filename VARCHAR(255) NOT NULL,
                file_size BIGINT NOT NULL,
                content_type VARCHAR(100),
                file_path VARCHAR(500),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✅ mail_attachments 테이블 생성 완료")
        
        # 6. 기본 조직 데이터 삽입
        print("📋 6. 기본 조직 데이터 삽입...")
        cursor.execute("""
            INSERT INTO organizations (org_id, org_code, name, subdomain)
            VALUES ('default-org-001', 'DEFAULT', 'Default Organization', 'default')
            ON CONFLICT (org_id) DO NOTHING;
        """)
        print("✅ 기본 조직 데이터 삽입 완료")
        
        # 변경사항 커밋
        conn.commit()
        
        # 생성된 테이블 확인
        print("\n📊 생성된 테이블 확인:")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        for table in tables:
            print(f"   - {table[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 모든 테이블 생성 완료!")
        
    except Exception as e:
        print(f"❌ 테이블 생성 실패: {e}")
        import traceback
        traceback.print_exc()

def main():
    """메인 함수"""
    print("🚀 SQL 테이블 생성 시작")
    print(f"⏰ 시작 시간: {datetime.now()}")
    
    create_tables_sql()
    
    print(f"\n⏰ 완료 시간: {datetime.now()}")

if __name__ == "__main__":
    main()