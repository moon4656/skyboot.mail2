#!/usr/bin/env python3
"""
실제 존재하는 사용자를 확인하는 스크립트
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json

def check_existing_users():
    """실제 존재하는 사용자를 확인합니다."""
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(
            host="localhost",
            database="skyboot_mail",
            user="skyboot_user",
            password="skyboot_password",
            port="5432"
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 최근 생성된 사용자 5명 조회
        print("📋 최근 생성된 사용자 5명:")
        cursor.execute("""
            SELECT 
                id,
                user_uuid,
                email,
                is_active,
                created_at,
                org_id
            FROM users 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        users = cursor.fetchall()
        for user in users:
            print(f"   - ID: {user['id']}, UUID: {user['user_uuid']}, Email: {user['email']}")
            print(f"     활성화: {user['is_active']}, 조직: {user['org_id']}, 생성일: {user['created_at']}")
            print()
        
        # 메일을 발송한 사용자 조회
        print("📤 메일을 발송한 사용자들:")
        cursor.execute("""
            SELECT DISTINCT 
                u.id,
                u.user_uuid,
                u.email,
                u.is_active,
                u.org_id,
                COUNT(m.mail_id) as sent_count
            FROM users u
            JOIN mail_users mu ON u.user_uuid = mu.user_uuid
            JOIN mails m ON mu.user_uuid = m.sender_uuid
            WHERE m.status = 'sent'
            GROUP BY u.id, u.user_uuid, u.email, u.is_active, u.org_id
            ORDER BY sent_count DESC
            LIMIT 5
        """)
        
        senders = cursor.fetchall()
        for sender in senders:
            print(f"   - Email: {sender['email']}, 발송 수: {sender['sent_count']}")
            print(f"     UUID: {sender['user_uuid']}, 활성화: {sender['is_active']}, 조직: {sender['org_id']}")
            print()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    check_existing_users()