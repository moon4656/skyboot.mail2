#!/usr/bin/env python3
"""
메일 사용자와 메일 발송자 UUID 매칭 확인 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.config import settings

def check_mail_user_mapping():
    """메일 사용자와 메일 발송자 UUID 매칭을 확인합니다."""
    print("🔍 메일 사용자 매칭 확인 시작")
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # 최근 메일과 해당 발송자의 메일 사용자 정보 조회
        query = text("""
            SELECT 
                m.mail_uuid,
                m.subject,
                m.sender_uuid as mail_sender_uuid,
                m.org_id as mail_org_id,
                mu.user_uuid as mail_user_uuid,
                mu.email as mail_user_email,
                mu.org_id as mail_user_org_id,
                u.user_uuid as user_table_uuid,
                u.email as user_table_email
            FROM mails m
            LEFT JOIN mail_users mu ON m.sender_uuid = mu.user_uuid AND m.org_id = mu.org_id
            LEFT JOIN users u ON m.sender_uuid = u.user_uuid
            WHERE m.status = 'sent'
            ORDER BY m.created_at DESC 
            LIMIT 3
        """)
        
        result = conn.execute(query)
        mappings = result.fetchall()
        
        print(f"📧 최근 발송 메일 매칭 정보 {len(mappings)}개:")
        for mapping in mappings:
            print(f"   - 메일 UUID: {mapping.mail_uuid}")
            print(f"     제목: {mapping.subject}")
            print(f"     메일 발송자 UUID: {mapping.mail_sender_uuid}")
            print(f"     메일 조직 ID: {mapping.mail_org_id}")
            print(f"     메일 사용자 UUID: {mapping.mail_user_uuid}")
            print(f"     메일 사용자 이메일: {mapping.mail_user_email}")
            print(f"     메일 사용자 조직 ID: {mapping.mail_user_org_id}")
            print(f"     사용자 테이블 UUID: {mapping.user_table_uuid}")
            print(f"     사용자 테이블 이메일: {mapping.user_table_email}")
            print(f"     UUID 매칭: {mapping.mail_sender_uuid == mapping.mail_user_uuid}")
            print(f"     조직 매칭: {mapping.mail_org_id == mapping.mail_user_org_id}")
            print()
        
        # 메일 사용자 테이블 전체 조회
        mail_users_query = text("""
            SELECT user_uuid, email, org_id, is_active
            FROM mail_users 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        mail_users_result = conn.execute(mail_users_query)
        mail_users = mail_users_result.fetchall()
        
        print("👥 최근 메일 사용자 5개:")
        for mail_user in mail_users:
            print(f"   - UUID: {mail_user.user_uuid}")
            print(f"     이메일: {mail_user.email}")
            print(f"     조직: {mail_user.org_id}")
            print(f"     활성화: {mail_user.is_active}")
            print()

if __name__ == "__main__":
    check_mail_user_mapping()