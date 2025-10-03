"""
mails 테이블 데이터 확인 스크립트
"""
import psycopg2
from datetime import datetime
import json

# 데이터베이스 연결 설정
DB_CONFIG = {
    'host': 'localhost',
    'database': 'skyboot_mail',
    'user': 'postgres',
    'password': 'safe70!!',
    'port': '5432',
    'client_encoding': 'utf8'
}

def check_mails_table():
    """mails 테이블의 데이터를 확인합니다."""
    
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("🔍 mails 테이블 데이터 확인")
        print("=" * 60)
        
        # 1. 테이블 존재 여부 확인
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'mails'
            );
        """)
        table_exists = cursor.fetchone()[0]
        print(f"📋 mails 테이블 존재: {table_exists}")
        
        if not table_exists:
            print("❌ mails 테이블이 존재하지 않습니다!")
            return
        
        # 2. 테이블 구조 확인
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'mails'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print(f"\n📊 mails 테이블 구조 ({len(columns)}개 컬럼):")
        for col in columns:
            print(f"   - {col[0]}: {col[1]} (nullable: {col[2]})")
        
        # 3. 전체 레코드 수 확인
        cursor.execute("SELECT COUNT(*) FROM mails;")
        total_count = cursor.fetchone()[0]
        print(f"\n📈 전체 메일 수: {total_count}")
        
        # 4. 최근 메일 확인 (최대 10개)
        cursor.execute("""
            SELECT mail_uuid, sender_uuid, subject, status, priority, 
                   created_at, sent_at, org_id
            FROM mails 
            ORDER BY created_at DESC 
            LIMIT 10;
        """)
        recent_mails = cursor.fetchall()
        
        if recent_mails:
            print(f"\n📧 최근 메일 목록 ({len(recent_mails)}개):")
            for i, mail in enumerate(recent_mails, 1):
                print(f"   {i}. UUID: {mail[0]}")
                print(f"      발신자: {mail[1]}")
                print(f"      제목: {mail[2]}")
                print(f"      상태: {mail[3]}")
                print(f"      우선순위: {mail[4]}")
                print(f"      생성시간: {mail[5]}")
                print(f"      발송시간: {mail[6]}")
                print(f"      조직ID: {mail[7]}")
                print()
        else:
            print("\n❌ mails 테이블에 데이터가 없습니다!")
        
        # 5. 오늘 발송된 메일 확인
        cursor.execute("""
            SELECT COUNT(*) FROM mails 
            WHERE DATE(created_at) = CURRENT_DATE;
        """)
        today_count = cursor.fetchone()[0]
        print(f"📅 오늘 발송된 메일 수: {today_count}")
        
        # 6. 상태별 메일 수 확인
        cursor.execute("""
            SELECT status, COUNT(*) 
            FROM mails 
            GROUP BY status;
        """)
        status_counts = cursor.fetchall()
        print(f"\n📊 상태별 메일 수:")
        for status, count in status_counts:
            print(f"   - {status}: {count}개")
        
        # 7. 조직별 메일 수 확인
        cursor.execute("""
            SELECT org_id, COUNT(*) 
            FROM mails 
            GROUP BY org_id;
        """)
        org_counts = cursor.fetchall()
        print(f"\n🏢 조직별 메일 수:")
        for org_id, count in org_counts:
            print(f"   - {org_id}: {count}개")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 데이터베이스 오류: {e}")

def check_mail_recipients_table():
    """mail_recipients 테이블도 함께 확인합니다."""
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\n" + "=" * 60)
        print("🔍 mail_recipients 테이블 데이터 확인")
        
        # 테이블 존재 여부 확인
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'mail_recipients'
            );
        """)
        table_exists = cursor.fetchone()[0]
        print(f"📋 mail_recipients 테이블 존재: {table_exists}")
        
        if not table_exists:
            print("❌ mail_recipients 테이블이 존재하지 않습니다!")
            return
        
        # 전체 레코드 수 확인
        cursor.execute("SELECT COUNT(*) FROM mail_recipients;")
        total_count = cursor.fetchone()[0]
        print(f"📈 전체 수신자 수: {total_count}")
        
        # 최근 수신자 확인
        cursor.execute("""
            SELECT mail_uuid, recipient_email, recipient_type, created_at
            FROM mail_recipients 
            ORDER BY created_at DESC 
            LIMIT 10;
        """)
        recent_recipients = cursor.fetchall()
        
        if recent_recipients:
            print(f"\n📧 최근 수신자 목록 ({len(recent_recipients)}개):")
            for i, recipient in enumerate(recent_recipients, 1):
                print(f"   {i}. 메일UUID: {recipient[0]}")
                print(f"      수신자: {recipient[1]}")
                print(f"      타입: {recipient[2]}")
                print(f"      생성시간: {recipient[3]}")
                print()
        else:
            print("\n❌ mail_recipients 테이블에 데이터가 없습니다!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ mail_recipients 테이블 확인 오류: {e}")

def check_mail_logs_table():
    """mail_logs 테이블도 확인합니다."""
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\n" + "=" * 60)
        print("🔍 mail_logs 테이블 데이터 확인")
        
        # 테이블 존재 여부 확인
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'mail_logs'
            );
        """)
        table_exists = cursor.fetchone()[0]
        print(f"📋 mail_logs 테이블 존재: {table_exists}")
        
        if not table_exists:
            print("❌ mail_logs 테이블이 존재하지 않습니다!")
            return
        
        # 전체 레코드 수 확인
        cursor.execute("SELECT COUNT(*) FROM mail_logs;")
        total_count = cursor.fetchone()[0]
        print(f"📈 전체 로그 수: {total_count}")
        
        # 최근 로그 확인
        cursor.execute("""
            SELECT mail_uuid, user_uuid, action, details, created_at
            FROM mail_logs 
            ORDER BY created_at DESC 
            LIMIT 10;
        """)
        recent_logs = cursor.fetchall()
        
        if recent_logs:
            print(f"\n📝 최근 로그 목록 ({len(recent_logs)}개):")
            for i, log in enumerate(recent_logs, 1):
                print(f"   {i}. 메일UUID: {log[0]}")
                print(f"      사용자UUID: {log[1]}")
                print(f"      액션: {log[2]}")
                print(f"      상세: {log[3]}")
                print(f"      생성시간: {log[4]}")
                print()
        else:
            print("\n❌ mail_logs 테이블에 데이터가 없습니다!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ mail_logs 테이블 확인 오류: {e}")

def main():
    """메인 함수"""
    print("🚀 메일 테이블 데이터 확인 시작")
    print(f"⏰ 확인 시간: {datetime.now()}")
    
    # 각 테이블 확인
    check_mails_table()
    check_mail_recipients_table()
    check_mail_logs_table()
    
    print("\n🎉 메일 테이블 확인 완료!")

if __name__ == "__main__":
    main()