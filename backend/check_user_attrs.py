import sys
sys.path.append('.')
from app.database import get_db
from app.service.auth_service import AuthService
from app.model.user_model import User
from sqlalchemy.orm import Session

# 데이터베이스 연결
db = next(get_db())

# admin01 사용자 조회
user = db.query(User).filter(User.user_id == 'admin01').first()
if user:
    print('사용자 정보:')
    print(f'  user_id: {user.user_id}')
    print(f'  email: {user.email}')
    print(f'  hasattr org_id: {hasattr(user, "org_id")}')
    if hasattr(user, 'org_id'):
        print(f'  org_id: {user.org_id}')
    print(f'  hasattr organization_id: {hasattr(user, "organization_id")}')
    if hasattr(user, 'organization_id'):
        print(f'  organization_id: {user.organization_id}')
    attrs = [attr for attr in dir(user) if not attr.startswith('_')]
    print(f'  모든 속성: {attrs}')
else:
    print('admin01 사용자를 찾을 수 없습니다.')

db.close()