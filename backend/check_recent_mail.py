#!/usr/bin/env python3
"""
최근 발송한 메일의 데이터베이스 저장 상태를 확인하는 스크립트
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json

def check_recent_mail():
    """최근 발송한 메일의 저장 상태를 확인합니다."""
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
        
        # 최근 생성된 메일 조회 (디버그 테스트 메일)
        print("📧 최근 생성된 메일 (디버그 테스트 메일):")
        cursor.execute("""
            SELECT 
                mail_id,
                subject,
                sender_uuid,
                status,
                org_id,
                created_at,
                sent_at
            FROM mails 
            WHERE subject LIKE '%디버그 테스트 메일%'
            ORDER BY created_at DESC 
            LIMIT 3
        """)
        
        recent_mails = cursor.fetchall()
        for mail in recent_mails:
            print(f"   - 메일 ID: {mail['mail_id']}")
            print(f"     제목: {mail['subject']}")
            print(f"     발송자 UUID: {mail['sender_uuid']}")
            print(f"     상태: {mail['status']}")
            print(f"     조직 ID: {mail['org_id']}")
            print(f"     생성일: {mail['created_at']}")
            print(f"     발송일: {mail['sent_at']}")
            print()
        
        if recent_mails:
            latest_mail = recent_mails[0]
            sender_uuid = latest_mail['sender_uuid']
            org_id = latest_mail['org_id']
            
            print(f"🔍 최신 메일의 발송자 정보 분석:")
            print(f"   - 발송자 UUID: {sender_uuid}")
            print(f"   - 조직 ID: {org_id}")
            
            # 해당 발송자의 사용자 정보 조회
            print("\n👤 발송자의 사용자 정보:")
            cursor.execute("""
                SELECT 
                    user_uuid,
                    email,
                    username,
                    org_id,
                    is_active
                FROM users 
                WHERE user_uuid = %s
            """, (sender_uuid,))
            
            user_info = cursor.fetchone()
            if user_info:
                print(f"   - 사용자 UUID: {user_info['user_uuid']}")
                print(f"   - 이메일: {user_info['email']}")
                print(f"   - 사용자명: {user_info['username']}")
                print(f"   - 조직 ID: {user_info['org_id']}")
                print(f"   - 활성화: {user_info['is_active']}")
            else:
                print(f"   ❌ 발송자 UUID({sender_uuid})에 해당하는 사용자를 찾을 수 없습니다!")
            
            # 보낸 메일함 쿼리 시뮬레이션
            print(f"\n🔍 보낸 메일함 쿼리 시뮬레이션:")
            print(f"   - 쿼리 조건: sender_uuid = '{sender_uuid}' AND status = 'sent' AND org_id = '{org_id}'")
            
            cursor.execute("""
                SELECT 
                    mail_id,
                    subject,
                    sender_uuid,
                    status,
                    org_id,
                    sent_at
                FROM mails 
                WHERE sender_uuid = %s 
                AND status = 'sent' 
                AND org_id = %s
                ORDER BY sent_at DESC
            """, (sender_uuid, org_id))
            
            sent_mails = cursor.fetchall()
            print(f"   - 조회된 보낸 메일 수: {len(sent_mails)}")
            
            if sent_mails:
                print("   - 보낸 메일 목록:")
                for mail in sent_mails:
                    print(f"     * {mail['subject']} (ID: {mail['mail_id']}, 발송일: {mail['sent_at']})")
            else:
                print("   ❌ 보낸 메일함 쿼리 결과가 비어있습니다!")
                
                # 각 조건별로 확인
                print("\n🔍 조건별 확인:")
                
                # sender_uuid 조건만
                cursor.execute("SELECT COUNT(*) as count FROM mails WHERE sender_uuid = %s", (sender_uuid,))
                count1 = cursor.fetchone()['count']
                print(f"   - sender_uuid = '{sender_uuid}': {count1}개")
                
                # status 조건만
                cursor.execute("SELECT COUNT(*) as count FROM mails WHERE status = 'sent'")
                count2 = cursor.fetchone()['count']
                print(f"   - status = 'sent': {count2}개")
                
                # org_id 조건만
                cursor.execute("SELECT COUNT(*) as count FROM mails WHERE org_id = %s", (org_id,))
                count3 = cursor.fetchone()['count']
                print(f"   - org_id = '{org_id}': {count3}개")
                
                # sender_uuid + status
                cursor.execute("SELECT COUNT(*) as count FROM mails WHERE sender_uuid = %s AND status = 'sent'", (sender_uuid,))
                count4 = cursor.fetchone()['count']
                print(f"   - sender_uuid + status: {count4}개")
                
                # sender_uuid + org_id
                cursor.execute("SELECT COUNT(*) as count FROM mails WHERE sender_uuid = %s AND org_id = %s", (sender_uuid, org_id))
                count5 = cursor.fetchone()['count']
                print(f"   - sender_uuid + org_id: {count5}개")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    check_recent_mail()