#!/usr/bin/env python3
"""
간단한 메일 상태 확인 스크립트
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings

def check_recent_mails():
    """최근 메일 상태를 확인합니다."""
    try:
        # 데이터베이스 연결
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("📧 최근 생성된 메일 (디버그 테스트 메일):")
        
        # 최근 디버그 테스트 메일 조회
        result = db.execute(text("""
            SELECT 
                mail_uuid,
                subject,
                sender_uuid,
                status,
                org_id,
                created_at
            FROM mails 
            WHERE subject LIKE '%디버그 테스트 메일%'
            ORDER BY created_at DESC 
            LIMIT 3
        """))
        
        mails = result.fetchall()
        
        if not mails:
            print("   ❌ 디버그 테스트 메일을 찾을 수 없습니다.")
            return
        
        for mail in mails:
            print(f"   - 메일 UUID: {mail.mail_uuid}")
            print(f"     제목: {mail.subject}")
            print(f"     발송자 UUID: {mail.sender_uuid}")
            print(f"     상태: {mail.status}")
            print(f"     조직 ID: {mail.org_id}")
            print(f"     생성일: {mail.created_at}")
            print()
        
        # 최신 메일로 보낸 메일함 쿼리 테스트
        latest_mail = mails[0]
        sender_uuid = latest_mail.sender_uuid
        org_id = latest_mail.org_id
        
        print(f"🔍 보낸 메일함 쿼리 테스트:")
        print(f"   - 발송자 UUID: {sender_uuid}")
        print(f"   - 조직 ID: {org_id}")
        
        # 보낸 메일함 쿼리 실행
        sent_result = db.execute(text("""
            SELECT 
                mail_uuid,
                subject,
                sender_uuid,
                status,
                org_id
            FROM mails 
            WHERE sender_uuid = :sender_uuid 
            AND status = 'sent' 
            AND org_id = :org_id
            ORDER BY created_at DESC
        """), {"sender_uuid": sender_uuid, "org_id": org_id})
        
        sent_mails = sent_result.fetchall()
        print(f"   - 보낸 메일함 쿼리 결과: {len(sent_mails)}개")
        
        if sent_mails:
            for mail in sent_mails:
                print(f"     * {mail.subject} (상태: {mail.status})")
        else:
            print("   ❌ 보낸 메일함에서 메일을 찾을 수 없습니다!")
            
            # 조건별 확인
            print("\n🔍 조건별 메일 수 확인:")
            
            # sender_uuid만
            count1 = db.execute(text("SELECT COUNT(*) as count FROM mails WHERE sender_uuid = :sender_uuid"), 
                               {"sender_uuid": sender_uuid}).fetchone().count
            print(f"   - sender_uuid 일치: {count1}개")
            
            # status만
            count2 = db.execute(text("SELECT COUNT(*) as count FROM mails WHERE status = 'sent'")).fetchone().count
            print(f"   - status = 'sent': {count2}개")
            
            # org_id만
            count3 = db.execute(text("SELECT COUNT(*) as count FROM mails WHERE org_id = :org_id"), 
                               {"org_id": org_id}).fetchone().count
            print(f"   - org_id 일치: {count3}개")
            
            # 최신 메일의 실제 상태 확인
            actual_status = db.execute(text("SELECT status FROM mails WHERE mail_uuid = :mail_uuid"), 
                                     {"mail_uuid": latest_mail.mail_uuid}).fetchone().status
            print(f"   - 최신 메일의 실제 상태: '{actual_status}'")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_recent_mails()