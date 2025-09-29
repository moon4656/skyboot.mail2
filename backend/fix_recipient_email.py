#!/usr/bin/env python3
"""
mail_convenience_router.py에서 recipient_email을 recipient_uuid로 일괄 변경하는 스크립트
"""

import re

def fix_recipient_email():
    """recipient_email을 recipient_uuid로 변경"""
    
    file_path = "app/router/mail_convenience_router.py"
    
    try:
        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 원본 내용 백업
        backup_path = file_path + ".backup"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 원본 파일 백업: {backup_path}")
        
        # 변경 전 개수 확인
        before_count = len(re.findall(r'MailRecipient\.recipient_email == mail_user\.email', content))
        print(f"📊 변경 전 recipient_email 사용 개수: {before_count}")
        
        # 패턴 변경
        # MailRecipient.recipient_email == mail_user.email -> MailRecipient.recipient_uuid == mail_user.user_uuid
        content = re.sub(
            r'MailRecipient\.recipient_email == mail_user\.email',
            'MailRecipient.recipient_uuid == mail_user.user_uuid',
            content
        )
        
        # 변경 후 개수 확인
        after_count = len(re.findall(r'MailRecipient\.recipient_uuid == mail_user\.user_uuid', content))
        print(f"📊 변경 후 recipient_uuid 사용 개수: {after_count}")
        
        # 파일 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 파일 수정 완료: {file_path}")
        print(f"📈 총 {before_count}개의 패턴이 변경되었습니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔧 recipient_email -> recipient_uuid 일괄 변경 시작")
    fix_recipient_email()