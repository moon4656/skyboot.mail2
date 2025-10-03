"""
SQLAlchemy를 사용해서 직접 테이블을 생성하는 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from app.model.user_model import Base as UserBase
from app.model.organization_model import Base as OrgBase  
from app.model.mail_model import Base as MailBase
from app.config import settings

def create_all_tables():
    """모든 테이블을 생성합니다."""
    
    print("🚀 SQLAlchemy를 사용한 테이블 생성 시작")
    print(f"📊 데이터베이스 URL: {settings.DATABASE_URL}")
    
    # 데이터베이스 엔진 생성
    engine = create_engine(settings.DATABASE_URL, echo=True)  # SQL 로그 출력
    
    try:
        print("📋 사용자 관련 테이블 생성...")
        print(f"   테이블 목록: {list(UserBase.metadata.tables.keys())}")
        UserBase.metadata.create_all(bind=engine)
        print("✅ 사용자 테이블 생성 완료")
        
        print("📋 조직 관련 테이블 생성...")
        print(f"   테이블 목록: {list(OrgBase.metadata.tables.keys())}")
        OrgBase.metadata.create_all(bind=engine)
        print("✅ 조직 테이블 생성 완료")
        
        print("📋 메일 관련 테이블 생성...")
        print(f"   테이블 목록: {list(MailBase.metadata.tables.keys())}")
        MailBase.metadata.create_all(bind=engine)
        print("✅ 메일 테이블 생성 완료")
        
        print("🎉 모든 테이블 생성 완료!")
        
        # 생성된 테이블 확인
        print("\n📊 생성된 테이블 확인:")
        with engine.connect() as conn:
            result = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
            tables = result.fetchall()
            for table in tables:
                print(f"   - {table[0]}")
        
    except Exception as e:
        print(f"❌ 테이블 생성 실패: {e}")
        import traceback
        traceback.print_exc()

def main():
    """메인 함수"""
    create_all_tables()

if __name__ == "__main__":
    main()