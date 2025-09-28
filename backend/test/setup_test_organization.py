#!/usr/bin/env python3
"""
테스트용 조직 설정 스크립트 (실제 DB 구조 기반)
"""

import psycopg2
from app.config import settings
import uuid

def setup_test_organization():
    """테스트용 조직을 설정합니다."""
    try:
        print("🏢 테스트용 조직 설정 시작...")
        
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            port=settings.DB_PORT
        )
        cursor = conn.cursor()
        
        # 기존 조직 확인
        cursor.execute("SELECT COUNT(*) FROM organizations")
        org_count = cursor.fetchone()[0]
        
        if org_count > 0:
            print(f"✅ 이미 {org_count}개의 조직이 존재합니다.")
            cursor.execute("SELECT id, name, domain FROM organizations LIMIT 1")
            org = cursor.fetchone()
            print(f"   첫 번째 조직: ID={org[0]}, 이름={org[1]}, 도메인={org[2]}")
        else:
            # 새 조직 생성
            org_uuid = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO organizations (organization_uuid, name, domain, description, is_active)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, name, domain
            """, (
                org_uuid,
                "테스트 조직",
                "test.skyboot.mail",
                "테스트용 기본 조직",
                True
            ))
            
            new_org = cursor.fetchone()
            conn.commit()
            print(f"✅ 새 조직 생성 완료: ID={new_org[0]}, 이름={new_org[1]}, 도메인={new_org[2]}")
        
        cursor.close()
        conn.close()
        print("🎉 조직 설정 완료!")
        
    except Exception as e:
        print(f"❌ 조직 설정 중 오류 발생: {e}")
        print("❌ 조직 설정 실패")

if __name__ == "__main__":
    setup_test_organization()