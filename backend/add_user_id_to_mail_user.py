#!/usr/bin/env python3
"""
MailUser 테이블에 user_id 컬럼을 추가하는 마이그레이션 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, String, ForeignKey, Column
from app.database.base import engine, SessionLocal
from app.model.base_model import User
from app.model.mail_model import MailUser

def add_user_id_column():
    """MailUser 테이블에 user_id 컬럼 추가"""
    print("🔧 MailUser 테이블에 user_id 컬럼 추가 중...")
    
    db = SessionLocal()
    try:
        # 1. user_id 컬럼 추가
        print("1. user_id 컬럼 추가...")
        with engine.connect() as conn:
            # 컬럼이 이미 존재하는지 확인
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'mail_users' AND column_name = 'user_id'
            """))
            
            if result.fetchone() is None:
                # user_id 컬럼 추가
                conn.execute(text("""
                    ALTER TABLE mail_users 
                    ADD COLUMN user_id VARCHAR(36)
                """))
                conn.commit()
                print("✅ user_id 컬럼이 추가되었습니다.")
            else:
                print("ℹ️ user_id 컬럼이 이미 존재합니다.")
        
        # 2. 기존 MailUser와 User를 이메일로 매칭하여 user_id 설정
        print("2. 기존 데이터 매칭...")
        
        # 모든 MailUser 조회
        mail_users = db.query(MailUser).all()
        print(f"총 {len(mail_users)}개의 MailUser 발견")
        
        updated_count = 0
        for mail_user in mail_users:
            if mail_user.user_id is None:  # user_id가 없는 경우만
                # 같은 이메일을 가진 User 찾기
                user = db.query(User).filter(User.email == mail_user.email).first()
                if user:
                    mail_user.user_id = user.id
                    updated_count += 1
                    print(f"  MailUser {mail_user.email} -> User {user.id}")
        
        if updated_count > 0:
            db.commit()
            print(f"✅ {updated_count}개의 MailUser에 user_id가 설정되었습니다.")
        else:
            print("ℹ️ 매칭할 데이터가 없습니다.")
        
        # 3. 외래키 제약조건 추가
        print("3. 외래키 제약조건 추가...")
        with engine.connect() as conn:
            try:
                conn.execute(text("""
                    ALTER TABLE mail_users 
                    ADD CONSTRAINT fk_mail_users_user_id 
                    FOREIGN KEY (user_id) REFERENCES users(id)
                """))
                conn.commit()
                print("✅ 외래키 제약조건이 추가되었습니다.")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("ℹ️ 외래키 제약조건이 이미 존재합니다.")
                else:
                    print(f"⚠️ 외래키 제약조건 추가 실패: {e}")
        
        # 4. 최종 확인
        print("4. 최종 확인...")
        mail_users = db.query(MailUser).all()
        for mail_user in mail_users:
            print(f"  ID: {mail_user.id}, Email: {mail_user.email}, UserID: {mail_user.user_id}")
        
        print("✅ MailUser 테이블 user_id 컬럼 추가 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_user_id_column()