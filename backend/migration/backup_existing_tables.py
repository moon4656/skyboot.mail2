#!/usr/bin/env python3
"""
기존 테이블 데이터를 백업하는 스크립트
"""

import psycopg2
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def backup_table_data():
    """모든 테이블의 데이터를 JSON 형태로 백업합니다."""
    
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'skyboot_mail'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'password'),
            port=os.getenv('DB_PORT', '5432')
        )
        
        cursor = conn.cursor()
        
        # 백업 디렉토리 생성
        backup_dir = "table_backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print("💾 기존 테이블 데이터 백업 시작...")
        print("=" * 60)
        
        # 모든 테이블 목록 조회
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        backup_data = {}
        
        for (table_name,) in tables:
            try:
                print(f"📋 {table_name} 테이블 백업 중...")
                
                # 테이블의 모든 데이터 조회
                cursor.execute(f"SELECT * FROM {table_name};")
                rows = cursor.fetchall()
                
                # 컬럼 정보 조회
                cursor.execute(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    ORDER BY ordinal_position;
                """)
                columns_info = cursor.fetchall()
                column_names = [col[0] for col in columns_info]
                
                # 데이터를 딕셔너리 형태로 변환
                table_data = []
                for row in rows:
                    row_dict = {}
                    for i, value in enumerate(row):
                        # datetime 객체를 문자열로 변환
                        if hasattr(value, 'isoformat'):
                            value = value.isoformat()
                        row_dict[column_names[i]] = value
                    table_data.append(row_dict)
                
                backup_data[table_name] = {
                    'columns': column_names,
                    'data': table_data,
                    'record_count': len(table_data)
                }
                
                print(f"   ✅ {len(table_data)}개 레코드 백업 완료")
                
            except Exception as e:
                print(f"   ❌ {table_name} 백업 오류: {e}")
                backup_data[table_name] = {
                    'error': str(e),
                    'record_count': 0
                }
        
        # 백업 파일 저장
        backup_filename = f"{backup_dir}/table_backup_{timestamp}.json"
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        # 백업 요약 정보 저장
        summary = {
            'backup_time': timestamp,
            'total_tables': len(tables),
            'total_records': sum(table['record_count'] for table in backup_data.values() if 'record_count' in table),
            'backup_file': backup_filename,
            'tables': {name: data.get('record_count', 0) for name, data in backup_data.items()}
        }
        
        summary_filename = f"{backup_dir}/backup_summary_{timestamp}.json"
        with open(summary_filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        cursor.close()
        conn.close()
        
        print()
        print("=" * 60)
        print("✅ 테이블 데이터 백업 완료!")
        print(f"📁 백업 파일: {backup_filename}")
        print(f"📊 요약 파일: {summary_filename}")
        print(f"📋 총 {summary['total_tables']}개 테이블, {summary['total_records']}개 레코드 백업")
        
        return backup_filename, summary_filename
        
    except Exception as e:
        print(f"❌ 백업 오류: {e}")
        return None, None

if __name__ == "__main__":
    backup_table_data()