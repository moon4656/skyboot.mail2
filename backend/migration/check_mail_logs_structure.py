from app.database import engine
from sqlalchemy import text

# mail_logs 테이블 구조 확인
with engine.connect() as conn:
    try:
        # PostgreSQL에서 테이블 구조 확인
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'mail_logs' 
            ORDER BY ordinal_position;
        """))
        
        columns = result.fetchall()
        print('mail_logs 테이블 구조:')
        for column_name, data_type, is_nullable in columns:
            print(f'- {column_name}: {data_type} (nullable: {is_nullable})')
        
        # 데이터 확인
        result = conn.execute(text('SELECT COUNT(*) FROM mail_logs;'))
        count = result.scalar()
        print(f'\nmail_logs 테이블 레코드 수: {count}')
        
        if count > 0:
            # 첫 번째 레코드 확인
            result = conn.execute(text('SELECT * FROM mail_logs LIMIT 1;'))
            first_record = result.fetchone()
            print(f'첫 번째 레코드: {first_record}')
        
    except Exception as e:
        print(f'오류 발생: {e}')