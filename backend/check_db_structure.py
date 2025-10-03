"""
현재 데이터베이스 테이블 구조 확인 스크립트
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

def check_database_structure():
    """데이터베이스의 전체 구조를 확인합니다."""
    
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("🔍 데이터베이스 구조 확인")
        print("=" * 60)
        
        # 1. 모든 테이블 목록 확인
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        print(f"📋 전체 테이블 목록 ({len(tables)}개):")
        for table in tables:
            print(f"   - {table[0]}")
        
        print("\n" + "=" * 60)
        
        # 2. 각 테이블의 구조 확인
        for table in tables:
            table_name = table[0]
            print(f"\n📊 {table_name} 테이블 구조:")
            
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            columns = cursor.fetchall()
            
            for col in columns:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                default = f" DEFAULT {col[3]}" if col[3] else ""
                print(f"   - {col[0]}: {col[1]} {nullable}{default}")
            
            # 테이블 레코드 수 확인
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"   📈 레코드 수: {count}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 데이터베이스 오류: {e}")

def main():
    """메인 함수"""
    print("🚀 데이터베이스 구조 확인 시작")
    print(f"⏰ 확인 시간: {datetime.now()}")
    
    check_database_structure()
    
    print("\n🎉 데이터베이스 구조 확인 완료!")

if __name__ == "__main__":
    main()