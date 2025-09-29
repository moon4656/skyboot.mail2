#!/usr/bin/env python3
"""
mail_core_router.py에서 recipient_email을 recipient_uuid로 수정하는 스크립트
"""

import re
import shutil
from pathlib import Path

def fix_mail_core_router():
    """mail_core_router.py의 recipient_email 사용 부분을 수정합니다."""
    
    file_path = Path("app/router/mail_core_router.py")
    backup_path = Path("app/router/mail_core_router.py.backup")
    
    # 백업 생성
    shutil.copy2(file_path, backup_path)
    print(f"✅ 백업 파일 생성: {backup_path}")
    
    # 파일 읽기
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 수정 전 recipient_email 개수 확인
    before_count = content.count('recipient_email')
    print(f"📊 수정 전 recipient_email 개수: {before_count}")
    
    # 패턴 수정
    patterns = [
        # r.recipient_email 패턴
        (r'r\.recipient_email', 'r.recipient.email'),
        # MailRecipient.recipient_email == mail_user.email 패턴
        (r'MailRecipient\.recipient_email\s*==\s*mail_user\.email', 'MailRecipient.recipient_uuid == mail_user.user_uuid'),
        # recipients에서 recipient_email 접근 패턴
        (r'recipients\s*=.*?\.all\(\)\s*\n.*?to_emails\s*=\s*\[r\.recipient_email.*?\]', 
         lambda m: m.group(0).replace('r.recipient_email', 'r.recipient.email')),
    ]
    
    modified_count = 0
    for pattern, replacement in patterns:
        if callable(replacement):
            # 복잡한 패턴의 경우 함수로 처리
            matches = list(re.finditer(pattern, content, re.DOTALL))
            for match in reversed(matches):  # 뒤에서부터 수정
                content = content[:match.start()] + replacement(match) + content[match.end():]
                modified_count += 1
        else:
            # 단순 패턴 교체
            new_content = re.sub(pattern, replacement, content)
            count = len(re.findall(pattern, content))
            modified_count += count
            content = new_content
    
    # 특별히 처리해야 할 부분들을 직접 수정
    # to_emails, cc_emails, bcc_emails 생성 부분
    content = re.sub(
        r'to_emails\s*=\s*\[r\.recipient_email\s+for\s+r\s+in\s+recipients\s+if\s+r\.recipient_type\s*==\s*RecipientType\.TO\]',
        'to_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.TO and r.recipient]',
        content
    )
    content = re.sub(
        r'cc_emails\s*=\s*\[r\.recipient_email\s+for\s+r\s+in\s+recipients\s+if\s+r\.recipient_type\s*==\s*RecipientType\.CC\]',
        'cc_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.CC and r.recipient]',
        content
    )
    content = re.sub(
        r'bcc_emails\s*=\s*\[r\.recipient_email\s+for\s+r\s+in\s+recipients\s+if\s+r\.recipient_type\s*==\s*RecipientType\.BCC\]',
        'bcc_emails = [r.recipient.email for r in recipients if r.recipient_type == RecipientType.BCC and r.recipient]',
        content
    )
    
    # 파일 쓰기
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 수정 후 개수 확인
    after_count = content.count('recipient_email')
    print(f"📊 수정 후 recipient_email 개수: {after_count}")
    print(f"🔧 총 {modified_count}개 패턴 수정 완료")
    
    print(f"✅ {file_path} 수정 완료")

if __name__ == "__main__":
    fix_mail_core_router()