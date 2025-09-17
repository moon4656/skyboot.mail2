from app.database import engine, SessionLocal
from app.models import User
from sqlalchemy import text

# 데이터베이스 스키마 변경 및 데이터 업데이트
with engine.connect() as conn:
    try:
        # 1. 임시 컬럼 생성
        print('1. 임시 컬럼 생성 중...')
        conn.execute(text('ALTER TABLE users ADD COLUMN temp_id VARCHAR(36);'))
        conn.commit()
        
        # 2. user_uuid 값을 temp_id에 복사
        print('2. UUID 값을 임시 컬럼에 복사 중...')
        conn.execute(text('UPDATE users SET temp_id = user_uuid;'))
        conn.commit()
        
        # 3. 기존 id 컬럼 삭제
        print('3. 기존 id 컬럼 삭제 중...')
        conn.execute(text('ALTER TABLE users DROP COLUMN id CASCADE;'))
        conn.commit()
        
        # 4. temp_id를 id로 이름 변경
        print('4. 임시 컬럼을 id로 이름 변경 중...')
        conn.execute(text('ALTER TABLE users RENAME COLUMN temp_id TO id;'))
        conn.commit()
        
        # 5. id 컬럼을 PRIMARY KEY로 설정
        print('5. id 컬럼을 PRIMARY KEY로 설정 중...')
        conn.execute(text('ALTER TABLE users ADD PRIMARY KEY (id);'))
        conn.commit()
        
        # 6. user_uuid 컬럼 삭제 (이제 id가 UUID 역할)
        print('6. user_uuid 컬럼 삭제 중...')
        conn.execute(text('ALTER TABLE users DROP COLUMN user_uuid;'))
        conn.commit()
        
        print('✅ 성공적으로 id 컬럼을 UUID로 변경했습니다!')
        
    except Exception as e:
        print(f'❌ 오류 발생: {e}')
        conn.rollback()

# 변경 결과 확인
print('\n변경 결과 확인:')
db = SessionLocal()
try:
    users = db.query(User).all()
    print(f'사용자 수: {len(users)}')
    for user in users:
        print(f'ID(UUID): {user.id}, Email: {user.email}')
except Exception as e:
    print(f'확인 중 오류: {e}')
finally:
    db.close()