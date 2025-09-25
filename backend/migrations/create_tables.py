#!/usr/bin/env python3
"""
데이터베이스 테이블 생성 스크립트

SQLAlchemy를 사용하여 모든 테이블을 생성합니다.
"""

import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from app.config import settings
from app.database.base import Base
# 모든 모델을 import하여 Base.metadata에 등록
from app.model.base_model import User, RefreshToken
from app.model.mail_model import MailUser, Mail, MailRecipient, MailAttachment, MailFolder, MailInFolder, MailLog

def create_tables():
    """
    모든 테이블을 생성합니다.
    """
    print("🚀 데이터베이스 테이블 생성 시작")
    print("=" * 50)
    
    try:
        # 데이터베이스 연결
        engine = create_engine(settings.DATABASE_URL)
        
        # 모든 테이블 생성
        print("📊 테이블 생성 중...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ 모든 테이블이 성공적으로 생성되었습니다!")
        
        # 생성된 테이블 목록 출력
        print("\n📋 생성된 테이블 목록:")
        for table_name in Base.metadata.tables.keys():
            print(f"   - {table_name}")
        
    except Exception as e:
        print(f"❌ 테이블 생성 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_tables()