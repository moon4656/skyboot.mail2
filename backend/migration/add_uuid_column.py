import uuid
from app.database import engine, SessionLocal
from app.models import User
from sqlalchemy import text

# user_uuid 컬럼 추가
with engine.connect() as conn:
    try:
        conn.execute(text('ALTER TABLE users ADD COLUMN user_uuid VARCHAR(36) UNIQUE;'))
        conn.commit()
        print('user_uuid 컬럼이 추가되었습니다.')
    except Exception as e:
        if 'already exists' in str(e) or '이미 존재' in str(e):
            print('user_uuid 컬럼이 이미 존재합니다.')
        else:
            print(f'컬럼 추가 중 오류: {e}')

# 기존 사용자들에게 UUID 할당
db = SessionLocal()
try:
    users = db.query(User).filter(User.user_uuid == None).all()
    for user in users:
        user.user_uuid = str(uuid.uuid4())
    db.commit()
    print(f'{len(users)}명의 사용자에게 UUID가 할당되었습니다.')
except Exception as e:
    print(f'UUID 할당 중 오류: {e}')
    db.rollback()
finally:
    db.close()