#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append('.')
from app.database.user import get_db
from app.model.user_model import User
from app.model.mail_model import Mail, MailUser
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, text
from datetime import datetime, timedelta

def check_uuid_mapping():
    """사용자 UUID와 메일 sender_uuid 매핑을 확인합니다."""
    db = next(get_db())
    
    try:
        print("🔍 사용자 UUID와 메일 sender_UUID 매핑 확인")
        print("=" * 60)
        
        # 최근 생성된 디버그 테스트 메일 조회
        recent_mails = db.execute(text("""
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
        """)).fetchall()
        
        print(f"📧 최근 디버그 테스트 메일: {len(recent_mails)}개")
        
        for mail in recent_mails:
            print(f"\n📨 메일 정보:")
            print(f"   - 메일 UUID: {mail.mail_uuid}")
            print(f"   - 제목: {mail.subject}")
            print(f"   - 발송자 UUID: {mail.sender_uuid}")
            print(f"   - 조직 ID: {mail.org_id}")
            print(f"   - 생성일: {mail.created_at}")
            
            # 해당 조직의 사용자들 조회
            users_in_org = db.execute(text("""
                SELECT 
                    u.user_uuid,
                    u.email,
                    u.username,
                    u.created_at as user_created_at
                FROM users u 
                WHERE u.org_id = :org_id
                ORDER BY u.created_at DESC
            """), {"org_id": mail.org_id}).fetchall()
            
            print(f"\n👥 해당 조직의 사용자들: {len(users_in_org)}명")
            for user in users_in_org:
                is_sender = user.user_uuid == mail.sender_uuid
                print(f"   - 사용자 UUID: {user.user_uuid} {'✅ (발송자)' if is_sender else ''}")
                print(f"     이메일: {user.email}")
                print(f"     사용자명: {user.username}")
                print(f"     생성일: {user.user_created_at}")
                print()
            
            # MailUser 테이블에서 해당 조직의 메일 사용자들 조회
            mail_users_in_org = db.execute(text("""
                SELECT 
                    user_uuid,
                    email,
                    display_name,
                    org_id,
                    created_at
                FROM mail_users 
                WHERE org_id = :org_id
                ORDER BY created_at DESC
            """), {"org_id": mail.org_id}).fetchall()
            
            print(f"\n📮 해당 조직의 메일 사용자들: {len(mail_users_in_org)}명")
            for mail_user in mail_users_in_org:
                is_sender = mail_user.user_uuid == mail.sender_uuid
                print(f"   - 메일 사용자 UUID: {mail_user.user_uuid} {'✅ (발송자)' if is_sender else ''}")
                print(f"     이메일: {mail_user.email}")
                print(f"     표시명: {mail_user.display_name}")
                print(f"     생성일: {mail_user.created_at}")
                print()
            
            # 보낸 메일함 쿼리 시뮬레이션
            print(f"🔍 보낸 메일함 쿼리 시뮬레이션:")
            sent_mails = db.execute(text("""
                SELECT 
                    m.mail_uuid,
                    m.subject,
                    m.sender_uuid,
                    m.status,
                    m.org_id,
                    mu.email as mail_user_email
                FROM mails m
                JOIN mail_users mu ON m.sender_uuid = mu.user_uuid AND m.org_id = mu.org_id
                WHERE m.sender_uuid = :sender_uuid 
                AND m.status = 'sent' 
                AND m.org_id = :org_id
                ORDER BY m.created_at DESC
            """), {"sender_uuid": mail.sender_uuid, "org_id": mail.org_id}).fetchall()
            
            print(f"   - 쿼리 결과: {len(sent_mails)}개")
            for sent_mail in sent_mails:
                print(f"     * {sent_mail.subject} (발송자: {sent_mail.mail_user_email})")
            
            print("-" * 60)
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_uuid_mapping()