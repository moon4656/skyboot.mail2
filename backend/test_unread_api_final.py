#!/usr/bin/env python3
"""
읽지 않은 메일 API 최종 테스트

올바른 user_id로 로그인하여 읽지 않은 메일 조회 API를 테스트합니다.
"""
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings

def get_db_session():
    """데이터베이스 세션 생성"""
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def login_user():
    """user01로 로그인하여 토큰 획득"""
    print("🔐 user01 로그인")
    print("=" * 60)
    
    login_data = {
        "user_id": "user01",  # 실제 user_id 사용
        "password": "test"
    }
    
    try:
        response = requests.post("http://localhost:8001/api/v1/auth/login", json=login_data)
        print(f"로그인 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            access_token = result.get("access_token")
            print(f"✅ 로그인 성공! 토큰: {access_token[:50]}...")
            return access_token
        else:
            print(f"❌ 로그인 실패: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 로그인 요청 실패: {e}")
        return None

def test_unread_mail_api(token):
    """읽지 않은 메일 조회 API 테스트"""
    if not token:
        print("\n❌ 토큰이 없어 읽지 않은 메일 API 테스트를 건너뜁니다.")
        return
    
    print(f"\n📧 읽지 않은 메일 조회 API 테스트")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get("http://localhost:8001/api/v1/mail/unread", headers=headers)
        print(f"읽지 않은 메일 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 읽지 않은 메일 조회 성공!")
            print(f"응답 데이터: {result}")
            
            # 응답 구조 분석
            if isinstance(result, dict):
                if "mails" in result:
                    mails = result["mails"]
                    pagination = result.get("pagination", {})
                    total = pagination.get("total", len(mails))
                    
                    print(f"   총 읽지 않은 메일 수: {total}")
                    print(f"   현재 페이지 메일 수: {len(mails)}")
                    
                    if mails:
                        print(f"   읽지 않은 메일 목록:")
                        for i, mail in enumerate(mails[:5]):  # 처음 5개만 표시
                            subject = mail.get('subject', 'N/A')
                            sender = mail.get('sender_email', 'N/A')
                            created_at = mail.get('created_at', 'N/A')
                            print(f"     {i+1}. {subject} (발송자: {sender}, 시간: {created_at})")
                    else:
                        print(f"   📭 읽지 않은 메일이 없습니다.")
                elif "count" in result:
                    count = result["count"]
                    print(f"   읽지 않은 메일 수: {count}")
                else:
                    print(f"   응답 형식을 분석할 수 없습니다: {result}")
            else:
                print(f"   예상과 다른 응답 형식: {type(result)} - {result}")
                
        else:
            print(f"❌ 읽지 않은 메일 조회 실패: {response.text}")
            
    except Exception as e:
        print(f"❌ 읽지 않은 메일 요청 실패: {e}")

def check_mail_folder_status():
    """메일 폴더 상태 확인"""
    print(f"\n📁 메일 폴더 상태 확인")
    print("=" * 60)
    
    try:
        db = get_db_session()
        
        # user01의 폴더 확인
        print("📋 user01의 메일 폴더:")
        result = db.execute(text("""
            SELECT folder_uuid, name, folder_type, is_system, created_at
            FROM mail_folders
            WHERE user_uuid = '3b959219-da10-42bb-9693-0aa3ed502cd3'
            ORDER BY folder_type;
        """))
        
        folders = result.fetchall()
        for folder in folders:
            print(f"  - {folder[1]} ({folder[2]}) - UUID: {folder[0][:8]}... - 시스템: {folder[3]}")
        
        # 각 폴더별 메일 수 확인
        print("\n📊 폴더별 메일 수:")
        for folder in folders:
            folder_uuid = folder[0]
            folder_name = folder[1]
            
            result = db.execute(text("""
                SELECT COUNT(*) as mail_count,
                       COUNT(CASE WHEN is_read = false THEN 1 END) as unread_count
                FROM mail_in_folders
                WHERE folder_uuid = :folder_uuid;
            """), {"folder_uuid": folder_uuid})
            
            counts = result.fetchone()
            total_count = counts[0]
            unread_count = counts[1]
            
            print(f"  - {folder_name}: 총 {total_count}개, 읽지 않음 {unread_count}개")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 메일 폴더 상태 확인 오류: {e}")

def move_some_mails_to_inbox():
    """테스트용으로 sent 폴더의 메일 일부를 inbox 폴더로 이동"""
    print(f"\n📦 테스트용 메일 이동 (sent → inbox)")
    print("=" * 60)
    
    try:
        db = get_db_session()
        
        # user01의 INBOX와 SENT 폴더 UUID 가져오기
        result = db.execute(text("""
            SELECT folder_uuid, folder_type
            FROM mail_folders
            WHERE user_uuid = '3b959219-da10-42bb-9693-0aa3ed502cd3'
            AND folder_type IN ('INBOX', 'SENT');
        """))
        
        folders = result.fetchall()
        inbox_uuid = None
        sent_uuid = None
        
        for folder in folders:
            if folder[1] == 'INBOX':
                inbox_uuid = folder[0]
            elif folder[1] == 'SENT':
                sent_uuid = folder[0]
        
        if not inbox_uuid or not sent_uuid:
            print(f"❌ INBOX 또는 SENT 폴더를 찾을 수 없습니다.")
            print(f"   INBOX UUID: {inbox_uuid}")
            print(f"   SENT UUID: {sent_uuid}")
            return
        
        print(f"📁 폴더 정보:")
        print(f"   INBOX UUID: {inbox_uuid}")
        print(f"   SENT UUID: {sent_uuid}")
        
        # SENT 폴더의 메일 중 처음 5개를 INBOX로 이동
        result = db.execute(text("""
            SELECT mail_uuid
            FROM mail_in_folders
            WHERE folder_uuid = :sent_uuid
            LIMIT 5;
        """), {"sent_uuid": sent_uuid})
        
        mails_to_move = result.fetchall()
        
        if not mails_to_move:
            print(f"❌ SENT 폴더에 이동할 메일이 없습니다.")
            return
        
        print(f"📦 {len(mails_to_move)}개 메일을 SENT에서 INBOX로 이동합니다...")
        
        for mail in mails_to_move:
            mail_uuid = mail[0]
            
            # 기존 SENT 폴더 레코드 삭제
            db.execute(text("""
                DELETE FROM mail_in_folders
                WHERE mail_uuid = :mail_uuid AND folder_uuid = :sent_uuid;
            """), {"mail_uuid": mail_uuid, "sent_uuid": sent_uuid})
            
            # INBOX 폴더에 새 레코드 추가 (읽지 않음으로 설정)
            db.execute(text("""
                INSERT INTO mail_in_folders (mail_uuid, folder_uuid, is_read, created_at)
                VALUES (:mail_uuid, :inbox_uuid, false, NOW());
            """), {"mail_uuid": mail_uuid, "inbox_uuid": inbox_uuid})
            
            print(f"   ✅ 메일 {mail_uuid[:8]}... 이동 완료")
        
        db.commit()
        print(f"✅ {len(mails_to_move)}개 메일 이동 완료!")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 메일 이동 오류: {e}")
        db.rollback()

def main():
    """메인 함수"""
    print("🔍 읽지 않은 메일 API 최종 테스트")
    print("=" * 60)
    
    # 1. 메일 폴더 상태 확인
    check_mail_folder_status()
    
    # 2. 테스트용 메일 이동
    move_some_mails_to_inbox()
    
    # 3. 로그인
    token = login_user()
    
    # 4. 읽지 않은 메일 API 테스트
    test_unread_mail_api(token)
    
    # 5. 이동 후 폴더 상태 재확인
    print(f"\n📁 이동 후 메일 폴더 상태 재확인")
    check_mail_folder_status()
    
    print("\n" + "=" * 60)
    print("🔍 읽지 않은 메일 API 최종 테스트 완료")

if __name__ == "__main__":
    main()