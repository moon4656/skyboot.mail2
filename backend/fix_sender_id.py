#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
라우터 파일들에서 sender_id를 sender_uuid로 변경하는 스크립트
"""

import os
import re

def fix_sender_id_in_file(file_path):
    """파일에서 sender_id를 sender_uuid로 변경"""
    print(f"Processing {file_path}...")
    
    try:
        # UTF-8로 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 변경 전 내용 백업
        original_content = content
        
        # sender_id를 sender_uuid로 변경
        content = content.replace('sender_id', 'sender_uuid')
        
        # MailUser.id를 MailUser.user_uuid로 변경
        content = content.replace('MailUser.user_uuid', 'MailUser.user_uuid')  # 이미 변경된 것은 그대로
        content = content.replace('MailUser.id', 'MailUser.user_uuid')
        
        # 변경사항이 있는 경우에만 파일 저장
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {file_path} 수정 완료")
            return True
        else:
            print(f"ℹ️ {file_path} 변경사항 없음")
            return False
            
    except Exception as e:
        print(f"❌ {file_path} 처리 중 오류: {e}")
        return False

def main():
    """메인 함수"""
    router_files = [
        'backend/app/router/mail_core_router.py',
        'backend/app/router/mail_convenience_router.py', 
        'backend/app/router/mail_advanced_router.py',
        'backend/app/router/mail_setup_router.py'
    ]
    
    success_count = 0
    
    for file_path in router_files:
        if os.path.exists(file_path):
            if fix_sender_id_in_file(file_path):
                success_count += 1
        else:
            print(f"⚠️ 파일을 찾을 수 없습니다: {file_path}")
    
    print(f"\n📊 처리 결과: {success_count}/{len(router_files)} 파일 수정 완료")

if __name__ == "__main__":
    main()