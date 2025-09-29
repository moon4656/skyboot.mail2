#!/usr/bin/env python3
"""
관리자 계정의 조직을 활성화하는 스크립트
"""

import psycopg2
from datetime import datetime

def activate_admin_organization():
    """관리자 계정의 조직을 활성화합니다."""
    
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="skybootmail",
            user="postgres",
            password="safe70!!"
        )
        
        print("✅ 데이터베이스 연결 성공!")
        
        cursor = conn.cursor()
        
        # admin@skyboot.kr 계정의 조직 ID 확인
        cursor.execute("""
        SELECT u.org_id, o.name, o.is_active
        FROM users u
        LEFT JOIN organizations o ON u.org_id = o.org_id
        WHERE u.email = %s
        """, ("admin@skyboot.kr",))
        
        result = cursor.fetchone()
        
        if result:
            org_id, org_name, is_active = result
            print(f"✅ 관리자 조직 정보:")
            print(f"   - 조직 ID: {org_id}")
            print(f"   - 조직명: {org_name}")
            print(f"   - 현재 활성화 상태: {is_active}")
            
            if not is_active:
                print(f"\n🔧 조직 활성화 중...")
                
                # 조직 활성화
                cursor.execute("""
                UPDATE organizations 
                SET is_active = true,
                    updated_at = %s
                WHERE org_id = %s
                """, (datetime.now(), org_id))
                
                conn.commit()
                
                print(f"✅ 조직이 활성화되었습니다.")
                
                # 활성화 확인
                cursor.execute("""
                SELECT is_active, name
                FROM organizations 
                WHERE org_id = %s
                """, (org_id,))
                
                updated_result = cursor.fetchone()
                print(f"   - 업데이트된 활성화 상태: {updated_result[0]}")
                print(f"   - 조직명: {updated_result[1]}")
                
            else:
                print(f"✅ 조직이 이미 활성화되어 있습니다.")
                
        else:
            print("❌ 관리자 계정을 찾을 수 없습니다.")
        
        # 모든 조직 상태 확인
        print(f"\n📋 전체 조직 목록:")
        cursor.execute("""
        SELECT org_id, name, domain, is_active, created_at
        FROM organizations
        ORDER BY created_at
        """)
        
        organizations = cursor.fetchall()
        for org in organizations:
            print(f"   - {org[1]} ({org[0][:8]}...): 활성화={org[3]}, 도메인={org[2]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")

if __name__ == "__main__":
    activate_admin_organization()