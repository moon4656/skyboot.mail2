from app.database.user import get_db
from app.model import User
from app.service.auth_service import AuthService
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# 새로운 비밀번호 해시 생성
new_password = 'admin123'
new_hash = pwd_context.hash(new_password)
print(f'New hash for password "{new_password}": {new_hash}')

# 데이터베이스 업데이트
db = next(get_db())
user = db.query(User).filter(User.user_id == 'admin07').first()
if user:
    user.hashed_password = new_hash
    db.commit()
    print(f'Password updated for user: {user.user_id}')
    
    # 검증 테스트
    verify_result = pwd_context.verify(new_password, new_hash)
    print(f'Verification test: {verify_result}')
else:
    print('User not found')