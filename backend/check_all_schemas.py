"""
모든 스키마의 테이블을 확인하는 스크립트
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

def check_all_schemas():
    """모든 스키마의 테이블을 확인합니다."""
    
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("🔍 모든 스키마의 테이블 확인")
        print("=" * 60)
        
        # 1. 모든 스키마 목록 확인
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            ORDER BY schema_name;
        """)
        schemas = cursor.fetchall()
        print(f"📋 스키마 목록 ({len(schemas)}개):")
        for schema in schemas:
            print(f"   - {schema[0]}")
        
        print("\n" + "=" * 60)
        
        # 2. 각 스키마의 테이블 확인
        for schema in schemas:
            schema_name = schema[0]
            print(f"\n📊 {schema_name} 스키마의 테이블:")
            
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                ORDER BY table_name;
            """, (schema_name,))
            tables = cursor.fetchall()
            
            if tables:
                for table in tables:
                    table_name = table[0]
                    # 테이블 레코드 수 확인
                    try:
                        cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}";')
                        count = cursor.fetchone()[0]
                        print(f"   - {table_name} ({count}개 레코드)")
                    except Exception as e:
                        print(f"   - {table_name} (레코드 수 확인 실패: {e})")
            else:
                print("   (테이블 없음)")
        
        # 3. 특정 테이블 검색
        print("\n" + "=" * 60)
        print("🔍 특정 테이블 검색:")
        
        search_tables = ['mails', 'mail_recipients', 'organizations', 'mail_users']
        for table_name in search_tables:
            cursor.execute("""
                SELECT table_schema, table_name 
                FROM information_schema.tables 
                WHERE table_name = %s;
            """, (table_name,))
            results = cursor.fetchall()
            
            if results:
                print(f"   📧 {table_name} 테이블 발견:")
                for result in results:
                    print(f"      - {result[0]}.{result[1]}")
            else:
                print(f"   ❌ {table_name} 테이블 없음")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 데이터베이스 오류: {e}")

def main():
    """메인 함수"""
    print("🚀 모든 스키마 테이블 확인 시작")
    print(f"⏰ 확인 시간: {datetime.now()}")
    
    check_all_schemas()
    
    print("\n🎉 모든 스키마 확인 완료!")

if __name__ == "__main__":
    main()