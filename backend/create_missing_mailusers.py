#!/usr/bin/env python3
"""
누락된 MailUser 레코드 생성 스크립트
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import uuid
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 데이터베이스 연결 설정
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/skyboot_mail")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_missing_mail_users():
    """누락된 MailUser 레코드 생성"""
    print("🔧 누락된 MailUser 레코드 생성 중...")
    
    db = SessionLocal()
    try:
        # 기존 사용자 중 MailUser가 없는 사용자 찾기
        result = db.execute(text("""
            SELECT u.user_id, u.email, u.org_id
            FROM users u
            LEFT JOIN mail_users mu ON u.user_id = mu.user_id
            WHERE mu.user_id IS NULL
            AND u.is_active = true
            ORDER BY u.created_at DESC
        """))
        
        users_without_mail_user = result.fetchall()
        
        if users_without_mail_user:
            print(f"📊 MailUser가 없는 사용자 {len(users_without_mail_user)}명 발견:")
            
            created_count = 0
            for user in users_without_mail_user:
                print(f"  - {user.email} (user_id: {user.user_id}, org_id: {user.org_id})")
                
                # MailUser 생성
                user_uuid = str(uuid.uuid4())
                display_name = user.email.split('@')[0]
                
                try:
                    db.execute(text("""
                        INSERT INTO mail_users (
                            user_id, user_uuid, org_id, email, 
                            password_hash, display_name, is_active, 
                            created_at, updated_at
                        ) VALUES (
                            :user_id, :user_uuid, :org_id, :email,
                            'temp_hash', :display_name, true,
                            NOW(), NOW()
                        )
                    """), {
                        'user_id': user.user_id,
                        'user_uuid': user_uuid,
                        'org_id': user.org_id,
                        'email': user.email,
                        'display_name': display_name
                    })
                    
                    print(f"    ✅ MailUser 생성 완료 (UUID: {user_uuid})")
                    created_count += 1
                    
                except Exception as e:
                    print(f"    ❌ MailUser 생성 실패: {str(e)}")
            
            if created_count > 0:
                db.commit()
                print(f"🎉 총 {created_count}명의 MailUser 생성 완료!")
            else:
                print("❌ MailUser 생성에 실패했습니다.")
        else:
            print("✅ 모든 사용자가 이미 MailUser를 가지고 있습니다.")
            
    except Exception as e:
        db.rollback()
        print(f"❌ MailUser 생성 오류: {str(e)}")
        import traceback
        print(f"상세 오류:\n{traceback.format_exc()}")
    finally:
        db.close()

def verify_mail_users():
    """MailUser 생성 결과 확인"""
    print("\n🔍 MailUser 생성 결과 확인 중...")
    
    db = SessionLocal()
    try:
        # debug_user로 시작하는 MailUser 조회
        result = db.execute(text("""
            SELECT 
                user_id,
                user_uuid,
                org_id,
                email,
                display_name,
                is_active,
                created_at
            FROM mail_users 
            WHERE email LIKE 'debug_user%'
            ORDER BY created_at DESC
        """))
        
        debug_mail_users = result.fetchall()
        
        if debug_mail_users:
            print(f"📊 debug_user MailUser {len(debug_mail_users)}개 발견:")
            for user in debug_mail_users:
                print(f"  - {user.email}")
                print(f"    user_id: {user.user_id}")
                print(f"    user_uuid: {user.user_uuid}")
                print(f"    org_id: {user.org_id}")
                print(f"    display_name: {user.display_name}")
                print(f"    is_active: {user.is_active}")
                print(f"    created_at: {user.created_at}")
                print("    ---")
        else:
            print("❌ debug_user MailUser가 없습니다!")
            
        # 전체 MailUser 수 확인
        result = db.execute(text("SELECT COUNT(*) as total FROM mail_users"))
        total_count = result.fetchone().total
        print(f"\n📊 전체 MailUser 수: {total_count}")
            
    except Exception as e:
        print(f"❌ MailUser 확인 오류: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 누락된 MailUser 레코드 생성 스크립트")
    print("=" * 50)
    
    # 1. 누락된 MailUser 생성
    create_missing_mail_users()
    
    # 2. 생성 결과 확인
    verify_mail_users()
    
    print("\n✅ 스크립트 완료!")