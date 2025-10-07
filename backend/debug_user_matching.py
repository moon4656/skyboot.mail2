#!/usr/bin/env python3
"""
사용자와 MailUser 매칭 상태 확인 스크립트
"""

import requests
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 데이터베이스 연결 설정
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/skyboot_mail")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def login_and_get_user_info():
    """로그인하여 사용자 정보 확인"""
    print("🔐 로그인 중...")
    
    # 로그인 요청
    login_data = {
        "user_id": "debug_user_1759709411@example.com",
        "password": "debug_password"
    }
    
    try:
        response = requests.post("http://localhost:8001/api/v1/auth/login", json=login_data)
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            user_info = result.get("user", {})
            
            print("✅ 로그인 성공")
            print(f"📊 사용자 정보:")
            print(f"  - user_id: {user_info.get('user_id')}")
            print(f"  - email: {user_info.get('email')}")
            print(f"  - org_id: {user_info.get('org_id')}")
            
            return token, user_info
        else:
            print(f"❌ 로그인 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"❌ 로그인 오류: {str(e)}")
        return None, None

def check_mailuser_matching(user_info):
    """사용자와 MailUser 매칭 확인"""
    if not user_info:
        return
        
    print(f"\n🔍 MailUser 매칭 확인 중...")
    print(f"찾을 사용자: user_id={user_info.get('user_id')}, org_id={user_info.get('org_id')}")
    
    db = SessionLocal()
    try:
        # 정확한 매칭 확인
        result = db.execute(text("""
            SELECT 
                user_id,
                user_uuid,
                org_id,
                email,
                display_name,
                is_active
            FROM mail_users 
            WHERE user_id = :user_id AND org_id = :org_id
        """), {
            'user_id': user_info.get('user_id'),
            'org_id': user_info.get('org_id')
        })
        
        mail_user = result.fetchone()
        
        if mail_user:
            print("✅ MailUser 매칭 성공:")
            print(f"  - user_id: {mail_user.user_id}")
            print(f"  - user_uuid: {mail_user.user_uuid}")
            print(f"  - org_id: {mail_user.org_id}")
            print(f"  - email: {mail_user.email}")
            print(f"  - display_name: {mail_user.display_name}")
            print(f"  - is_active: {mail_user.is_active}")
        else:
            print("❌ MailUser 매칭 실패!")
            
            # 비슷한 MailUser 찾기
            print("\n🔍 비슷한 MailUser 찾기:")
            
            # 같은 이메일로 찾기
            result = db.execute(text("""
                SELECT 
                    user_id,
                    user_uuid,
                    org_id,
                    email,
                    display_name,
                    is_active
                FROM mail_users 
                WHERE email = :email
            """), {
                'email': user_info.get('email')
            })
            
            similar_users = result.fetchall()
            
            if similar_users:
                print(f"📊 같은 이메일의 MailUser {len(similar_users)}개 발견:")
                for user in similar_users:
                    print(f"  - user_id: {user.user_id}")
                    print(f"    user_uuid: {user.user_uuid}")
                    print(f"    org_id: {user.org_id}")
                    print(f"    email: {user.email}")
                    print(f"    display_name: {user.display_name}")
                    print(f"    is_active: {user.is_active}")
                    print("    ---")
            else:
                print("❌ 같은 이메일의 MailUser도 없습니다!")
            
    except Exception as e:
        print(f"❌ MailUser 확인 오류: {str(e)}")
    finally:
        db.close()

def test_restore_with_debug():
    """디버그 정보와 함께 복원 테스트"""
    token, user_info = login_and_get_user_info()
    
    if not token:
        return
        
    check_mailuser_matching(user_info)
    
    print(f"\n📦 복원 테스트 (디버그 모드)...")
    
    # 간단한 테스트 백업 파일 생성
    import tempfile
    import zipfile
    
    test_mail_data = [
        {
            "mail_uuid": f"test-mail-{user_info.get('user_id', 'unknown')}",
            "subject": "테스트 메일",
            "body_text": "테스트 내용",
            "body_html": "<p>테스트 내용</p>",
            "sent_at": "2024-01-01T00:00:00",
            "recipients": [
                {
                    "recipient_email": "test@example.com",
                    "recipient_type": "TO"
                }
            ]
        }
    ]
    
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # JSON 파일 생성
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
                json.dump(test_mail_data, temp_file, indent=2, ensure_ascii=False, default=str)
                temp_file.flush()
                
                # ZIP에 추가
                zip_file.write(temp_file.name, 'mails.json')
                
                # 임시 파일 정리
                os.unlink(temp_file.name)
        
        print(f"✅ 테스트 백업 파일 생성: {temp_zip.name}")
        
        # 복원 요청
        try:
            with open(temp_zip.name, 'rb') as f:
                files = {'backup_file': ('test_backup.zip', f, 'application/zip')}
                data = {'overwrite_existing': 'false'}
                headers = {'Authorization': f'Bearer {token}'}
                
                response = requests.post(
                    "http://localhost:8001/api/v1/mail/advanced/restore",
                    files=files,
                    data=data,
                    headers=headers
                )
                
                print(f"응답 상태: {response.status_code}")
                print(f"응답: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
                
        except Exception as e:
            print(f"❌ 복원 요청 오류: {str(e)}")
        finally:
            # 임시 파일 정리
            os.unlink(temp_zip.name)

if __name__ == "__main__":
    print("🔧 사용자와 MailUser 매칭 디버그 스크립트")
    print("=" * 50)
    
    test_restore_with_debug()
    
    print("\n✅ 스크립트 완료!")