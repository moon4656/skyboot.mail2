#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append('.')
from app.database.user import get_db
from app.model.mail_model import Mail, MailInFolder, MailFolder, MailUser
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta

def check_sent_folder():
    """최근 발송된 메일의 보낸 메일함 배치 상태를 확인합니다."""
    
    # 데이터베이스 연결
    db = next(get_db())
    
    try:
        # 최근 1시간 내 발송된 메일 조회
        recent_time = datetime.now() - timedelta(hours=1)
        recent_mails = db.query(Mail).filter(
            Mail.created_at >= recent_time
        ).order_by(desc(Mail.created_at)).limit(5).all()
        
        print('📧 최근 발송된 메일:')
        for mail in recent_mails:
            print(f'  - 메일 UUID: {mail.mail_uuid}')
            print(f'  - 발송자 UUID: {mail.sender_uuid}')
            print(f'  - 제목: {mail.subject}')
            print(f'  - 상태: {mail.status}')
            print(f'  - 생성 시간: {mail.created_at}')
            
            # 발송자 정보 조회
            sender = db.query(MailUser).filter(MailUser.user_uuid == mail.sender_uuid).first()
            if sender:
                print(f'  - 발송자 이메일: {sender.email}')
                
                # 발송자의 보낸 메일함 조회
                sent_folder = db.query(MailFolder).filter(
                    and_(
                        MailFolder.user_uuid == sender.user_uuid,
                        MailFolder.folder_type == 'sent'
                    )
                ).first()
                
                if sent_folder:
                    print(f'  - 보낸 메일함 UUID: {sent_folder.folder_uuid}')
                    
                    # 메일이 보낸 메일함에 배치되었는지 확인
                    mail_in_folder = db.query(MailInFolder).filter(
                        and_(
                            MailInFolder.mail_uuid == mail.mail_uuid,
                            MailInFolder.folder_uuid == sent_folder.folder_uuid
                        )
                    ).first()
                    
                    if mail_in_folder:
                        print(f'  ✅ 보낸 메일함에 배치됨')
                    else:
                        print(f'  ❌ 보낸 메일함에 배치되지 않음')
                else:
                    print(f'  ❌ 보낸 메일함을 찾을 수 없음')
            else:
                print(f'  ❌ 발송자 정보를 찾을 수 없음')
            print()
            
    finally:
        db.close()

if __name__ == "__main__":
    check_sent_folder()