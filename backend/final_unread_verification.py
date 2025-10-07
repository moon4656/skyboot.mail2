#!/usr/bin/env python3
"""
읽지 않은 메일 기능 최종 검증

INBOX에 읽지 않은 메일이 있는 상태에서 
읽지 않은 메일 조회 API를 최종 검증합니다.
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

def check_current_mail_status():
    """현재 메일 상태 확인"""
    print("📊 현재 메일 상태 확인")
    print("=" * 60)
    
    user_uuid = '3b959219-da10-42bb-9693-0aa3ed502cd3'  # user01의 UUID
    
    try:
        db = get_db_session()
        
        # 폴더별 메일 수 확인
        result = db.execute(text("""
            SELECT 
                mf.name as folder_name,
                mf.folder_type,
                COUNT(mif.mail_uuid) as total_mails,
                COUNT(CASE WHEN mif.is_read = false THEN 1 END) as unread_mails
            FROM mail_folders mf
            LEFT JOIN mail_in_folders mif ON mf.folder_uuid = mif.folder_uuid
            WHERE mf.user_uuid = :user_uuid
            GROUP BY mf.folder_uuid, mf.name, mf.folder_type
            ORDER BY mf.folder_type;
        """), {"user_uuid": user_uuid})
        
        folders = result.fetchall()
        print("📁 폴더별 메일 현황:")
        total_unread = 0
        for folder in folders:
            folder_name = folder[0]
            folder_type = folder[1]
            total_mails = folder[2]
            unread_mails = folder[3]
            total_unread += unread_mails
            
            print(f"  - {folder_name} ({folder_type}): 총 {total_mails}개, 읽지 않음 {unread_mails}개")
        
        print(f"\n📧 전체 읽지 않은 메일 수: {total_unread}개")
        
        # INBOX의 읽지 않은 메일 상세 정보
        if total_unread > 0:
            result = db.execute(text("""
                SELECT 
                    m.mail_uuid,
                    m.subject,
                    m.sender_email,
                    m.created_at,
                    mif.is_read
                FROM mails m
                JOIN mail_in_folders mif ON m.mail_uuid = mif.mail_uuid
                JOIN mail_folders mf ON mif.folder_uuid = mf.folder_uuid
                WHERE mf.user_uuid = :user_uuid 
                AND mf.folder_type = 'inbox'
                AND mif.is_read = false
                ORDER BY m.created_at DESC
                LIMIT 5;
            """), {"user_uuid": user_uuid})
            
            unread_mails = result.fetchall()
            print(f"\n📋 INBOX의 읽지 않은 메일 목록:")
            for mail in unread_mails:
                mail_uuid = mail[0][:8]
                subject = mail[1]
                sender = mail[2]
                created_at = mail[3]
                is_read = mail[4]
                print(f"  - {mail_uuid}... | {subject} | {sender} | {created_at} | 읽음: {is_read}")
        
        db.close()
        return total_unread
        
    except Exception as e:
        print(f"❌ 메일 상태 확인 오류: {e}")
        return 0

def login_and_get_token():
    """로그인하여 토큰 획득"""
    print(f"\n🔐 user01 로그인")
    print("=" * 60)
    
    login_data = {
        "user_id": "user01",
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

def test_unread_mail_api_final(token):
    """읽지 않은 메일 API 최종 테스트"""
    if not token:
        print("\n❌ 토큰이 없어 읽지 않은 메일 API 테스트를 건너뜁니다.")
        return False
    
    print(f"\n📧 읽지 않은 메일 API 최종 테스트")
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
                if "data" in result:
                    data = result["data"]
                    mails = data.get("mails", [])
                    total = data.get("total", 0)
                    
                    print(f"\n📊 API 응답 분석:")
                    print(f"   총 읽지 않은 메일 수: {total}")
                    print(f"   현재 페이지 메일 수: {len(mails)}")
                    
                    if mails:
                        print(f"\n📋 읽지 않은 메일 목록:")
                        for i, mail in enumerate(mails):
                            subject = mail.get('subject', 'N/A')
                            sender = mail.get('sender_email', 'N/A')
                            created_at = mail.get('created_at', 'N/A')
                            is_read = mail.get('is_read', 'N/A')
                            print(f"     {i+1}. {subject}")
                            print(f"        발송자: {sender}")
                            print(f"        시간: {created_at}")
                            print(f"        읽음 상태: {is_read}")
                            print()
                        
                        return True
                    else:
                        print(f"   📭 API에서 읽지 않은 메일이 반환되지 않았습니다.")
                        return False
                else:
                    print(f"   예상과 다른 응답 구조: {result}")
                    return False
            else:
                print(f"   예상과 다른 응답 타입: {type(result)} - {result}")
                return False
                
        else:
            print(f"❌ 읽지 않은 메일 조회 실패: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 읽지 않은 메일 요청 실패: {e}")
        return False

def test_other_mail_apis(token):
    """다른 메일 API들도 테스트"""
    if not token:
        return
    
    print(f"\n📬 다른 메일 API 테스트")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # INBOX 조회
    try:
        response = requests.get("http://localhost:8001/api/v1/mail/inbox", headers=headers)
        print(f"INBOX 조회 상태: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            if "data" in result:
                inbox_count = result["data"].get("total", 0)
                print(f"✅ INBOX 총 메일 수: {inbox_count}개")
            else:
                print(f"✅ INBOX 조회 성공: {result}")
        else:
            print(f"❌ INBOX 조회 실패: {response.text}")
    except Exception as e:
        print(f"❌ INBOX 조회 오류: {e}")
    
    # SENT 조회
    try:
        response = requests.get("http://localhost:8001/api/v1/mail/sent", headers=headers)
        print(f"SENT 조회 상태: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            if "data" in result:
                sent_count = result["data"].get("total", 0)
                print(f"✅ SENT 총 메일 수: {sent_count}개")
            else:
                print(f"✅ SENT 조회 성공: {result}")
        else:
            print(f"❌ SENT 조회 실패: {response.text}")
    except Exception as e:
        print(f"❌ SENT 조회 오류: {e}")

def main():
    """메인 함수"""
    print("🔍 읽지 않은 메일 기능 최종 검증")
    print("=" * 60)
    
    # 1. 현재 메일 상태 확인
    unread_count = check_current_mail_status()
    
    # 2. 로그인
    token = login_and_get_token()
    
    # 3. 읽지 않은 메일 API 최종 테스트
    api_success = test_unread_mail_api_final(token)
    
    # 4. 다른 메일 API들도 테스트
    test_other_mail_apis(token)
    
    # 5. 최종 결과 요약
    print(f"\n" + "=" * 60)
    print("🎯 최종 검증 결과")
    print("=" * 60)
    print(f"📊 데이터베이스 읽지 않은 메일 수: {unread_count}개")
    print(f"🔌 읽지 않은 메일 API 성공: {'✅ 성공' if api_success else '❌ 실패'}")
    
    if unread_count > 0 and api_success:
        print(f"🎉 읽지 않은 메일 기능이 정상적으로 작동합니다!")
    elif unread_count > 0 and not api_success:
        print(f"⚠️ 데이터베이스에는 읽지 않은 메일이 있지만 API에서 조회되지 않습니다.")
    elif unread_count == 0:
        print(f"📭 현재 읽지 않은 메일이 없습니다.")
    
    print("\n" + "=" * 60)
    print("🔍 읽지 않은 메일 기능 최종 검증 완료")

if __name__ == "__main__":
    main()