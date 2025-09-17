from app.database import SessionLocal
from app.models import User

db = SessionLocal()
try:
    users = db.query(User).all()
    print(f'현재 사용자 수: {len(users)}')
    print('\n사용자 목록:')
    for user in users:
        print(f'ID: {user.id}, UUID: {user.user_uuid}, Email: {user.email}')
except Exception as e:
    print(f'오류 발생: {e}')
finally:
    db.close()