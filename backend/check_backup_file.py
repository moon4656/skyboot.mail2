#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
백업 파일 내용 확인 스크립트
"""

import zipfile
import json
import os

def check_backup_file():
    """백업 파일의 내용을 확인합니다."""
    backup_file = r'c:\Users\moon4\skyboot.mail2\backend\backups\mail_backup_user01@example.com_20251006_215423.zip'
    
    print("=" * 60)
    print("백업 파일 내용 확인")
    print("=" * 60)
    
    if os.path.exists(backup_file):
        print(f"백업 파일 존재: {backup_file}")
        print(f"파일 크기: {os.path.getsize(backup_file)} bytes")
        
        try:
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                print(f"ZIP 파일 내용: {zipf.namelist()}")
                
                if 'mails.json' in zipf.namelist():
                    json_content = zipf.read('mails.json').decode('utf-8')
                    print(f"mails.json 내용 길이: {len(json_content)} characters")
                    print("mails.json 내용:")
                    print("-" * 40)
                    print(json_content)
                    print("-" * 40)
                    
                    # JSON 파싱 시도
                    try:
                        mail_data = json.loads(json_content)
                        print(f"파싱된 데이터 타입: {type(mail_data)}")
                        
                        if isinstance(mail_data, list):
                            print(f"메일 개수: {len(mail_data)}")
                            if len(mail_data) > 0:
                                print("첫 번째 메일 샘플:")
                                print(json.dumps(mail_data[0], indent=2, ensure_ascii=False))
                        elif isinstance(mail_data, dict):
                            print(f"딕셔너리 키: {list(mail_data.keys())}")
                            if 'mails' in mail_data:
                                mails = mail_data['mails']
                                print(f"mails 키의 메일 개수: {len(mails)}")
                                if len(mails) > 0:
                                    print("첫 번째 메일 샘플:")
                                    print(json.dumps(mails[0], indent=2, ensure_ascii=False))
                            else:
                                print("전체 데이터 구조:")
                                print(json.dumps(mail_data, indent=2, ensure_ascii=False))
                    except json.JSONDecodeError as e:
                        print(f"JSON 파싱 오류: {e}")
                else:
                    print("mails.json 파일이 ZIP에 없습니다")
                    
        except Exception as e:
            print(f"ZIP 파일 읽기 오류: {e}")
    else:
        print(f"백업 파일이 존재하지 않습니다: {backup_file}")

if __name__ == "__main__":
    check_backup_file()