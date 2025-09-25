from app.database.base import engine, Base
from app.model.base_model import User, RefreshToken
from app.model.mail_model import MailLog

print("데이터베이스 테이블을 다시 생성합니다...")

# 모든 테이블 삭제
Base.metadata.drop_all(bind=engine)
print("기존 테이블 삭제 완료")

# 모든 테이블 생성
Base.metadata.create_all(bind=engine)
print("새 테이블 생성 완료")

print("테이블 재생성이 완료되었습니다.")