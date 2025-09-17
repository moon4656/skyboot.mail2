import sys
sys.path.append('.')

from sqlalchemy import create_engine, text
from app.config import settings

def check_database_encoding():
    """
    SQLAlchemy를 통해 데이터베이스 인코딩 설정을 확인합니다.
    """
    try:
        # SQLAlchemy 엔진 생성
        engine = create_engine(
            f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
            connect_args={"client_encoding": "utf8"}
        )
        
        with engine.connect() as conn:
            # 데이터베이스 인코딩 확인
            result = conn.execute(text("SHOW server_encoding;"))
            server_encoding = result.fetchone()[0]
            print(f"서버 인코딩: {server_encoding}")
            
            result = conn.execute(text("SHOW client_encoding;"))
            client_encoding = result.fetchone()[0]
            print(f"클라이언트 인코딩: {client_encoding}")
            
            # 데이터베이스 정보 확인
            result = conn.execute(text("""
                SELECT datname, encoding, datcollate, datctype 
                FROM pg_database 
                WHERE datname = :db_name;
            """), {"db_name": settings.DB_NAME})
            
            db_info = result.fetchone()
            if db_info:
                print(f"데이터베이스명: {db_info[0]}")
                print(f"인코딩 번호: {db_info[1]}")
                print(f"Collate: {db_info[2]}")
                print(f"Ctype: {db_info[3]}")
            
            # 실제 메일 데이터 확인 (바이너리 모드로)
            result = conn.execute(text("""
                SELECT id, to_email, 
                       length(subject) as subject_length,
                       length(body) as body_length,
                       subject, body
                FROM mail_logs 
                ORDER BY id DESC 
                LIMIT 3;
            """))
            
            print("\n=== 메일 로그 데이터 ====")
            for row in result.fetchall():
                print(f"ID: {row[0]}")
                print(f"수신자: {row[1]}")
                print(f"제목 (hex): {row[2]}")
                print(f"본문 (hex): {row[3]}")
                print(f"제목 (text): {row[4]}")
                print(f"본문 (text): {row[5]}")
                print("-" * 50)
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database_encoding()