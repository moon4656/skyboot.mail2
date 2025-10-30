#!/usr/bin/env python3
"""
기존 메일들의 폴더 할당 상태 확인 및 수정 스크립트 (현재 모델 구조 기준)

이 스크립트는 다음 작업을 수행합니다:
1. MailInFolder 관계가 없는 메일들을 찾습니다
2. 메일 상태에 따라 적절한 폴더에 자동 할당합니다
3. 발송된 메일 -> 보낸편지함
4. 수신된 메일 -> 받은편지함
"""

import sys
import os
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.user import get_db
from app.model.mail_model import Mail, MailUser, MailRecipient, MailFolder, MailInFolder, MailStatus, FolderType, RecipientType
from app.model.user_model import User
from app.model.organization_model import Organization

def fix_mail_folder_assignments():
    """기존 메일들의 폴더 할당 상태를 확인하고 수정합니다."""
    
    print("🔍 기존 메일들의 폴더 할당 상태 확인 및 수정 시작...")
    print("=" * 60)
    
    # 데이터베이스 세션 생성
    db = next(get_db())
    
    try:
        # 1. 전체 메일 수 확인
        total_mails = db.query(Mail).count()
        print(f"📊 전체 메일 수: {total_mails}")
        
        # 2. MailInFolder 관계가 있는 메일 수 확인
        mails_with_folder = db.query(Mail).join(MailInFolder, Mail.mail_uuid == MailInFolder.mail_uuid).count()
        print(f"📁 폴더에 할당된 메일 수: {mails_with_folder}")
        
        # 3. MailInFolder 관계가 없는 메일들 찾기
        mails_without_folder = db.query(Mail).outerjoin(MailInFolder, Mail.mail_uuid == MailInFolder.mail_uuid).filter(
            MailInFolder.mail_uuid.is_(None)
        ).all()
        
        unassigned_count = len(mails_without_folder)
        print(f"❌ 폴더에 할당되지 않은 메일 수: {unassigned_count}")
        
        if unassigned_count == 0:
            print("✅ 모든 메일이 이미 폴더에 할당되어 있습니다!")
            return
        
        print(f"\n🔧 {unassigned_count}개의 메일을 적절한 폴더에 할당합니다...")
        
        fixed_count = 0
        error_count = 0
        
        for mail in mails_without_folder:
            try:
                print(f"\n📧 처리 중: {mail.mail_uuid} - {mail.subject}")
                print(f"   상태: {mail.status}, 발송자: {mail.sender_uuid}")
                
                # 발송자 정보 조회
                sender_mail_user = db.query(MailUser).filter(MailUser.user_uuid == mail.sender_uuid).first()
                
                if not sender_mail_user:
                    print(f"   ❌ 발송자 MailUser를 찾을 수 없습니다: {mail.sender_uuid}")
                    error_count += 1
                    continue
                
                # 발송된 메일 처리
                if mail.status == MailStatus.SENT:
                    # 1. 발신자의 보낸편지함에 할당
                    sent_folder = db.query(MailFolder).filter(
                        and_(
                            MailFolder.user_uuid == sender_mail_user.user_uuid,
                            MailFolder.folder_type == FolderType.SENT
                        )
                    ).first()
                    
                    if sent_folder:
                        # 이미 할당되어 있는지 확인
                        existing_relation = db.query(MailInFolder).filter(
                            and_(
                                MailInFolder.mail_uuid == mail.mail_uuid,
                                MailInFolder.folder_uuid == sent_folder.folder_uuid,
                                MailInFolder.user_uuid == sender_mail_user.user_uuid
                            )
                        ).first()
                        
                        if not existing_relation:
                            mail_in_folder = MailInFolder(
                                mail_uuid=mail.mail_uuid,
                                folder_uuid=sent_folder.folder_uuid,
                                user_uuid=sender_mail_user.user_uuid
                            )
                            db.add(mail_in_folder)
                            print(f"   ✅ 발신자 보낸편지함에 할당: {sent_folder.folder_uuid}")
                            fixed_count += 1
                        else:
                            print(f"   ⚠️ 이미 발신자 보낸편지함에 할당됨")
                    else:
                        print(f"   ❌ 발신자 보낸편지함을 찾을 수 없습니다: {sender_mail_user.user_uuid}")
                        error_count += 1
                    
                    # 2. 수신자들의 받은편지함에 할당
                    recipients = db.query(MailRecipient).filter(MailRecipient.mail_uuid == mail.mail_uuid).all()
                    
                    for recipient in recipients:
                        # 수신자의 MailUser 정보 조회
                        recipient_mail_user = db.query(MailUser).filter(
                            and_(
                                MailUser.email == recipient.recipient_email,
                                MailUser.org_id == mail.org_id
                            )
                        ).first()
                        
                        if recipient_mail_user:
                            inbox_folder = db.query(MailFolder).filter(
                                and_(
                                    MailFolder.user_uuid == recipient_mail_user.user_uuid,
                                    MailFolder.folder_type == FolderType.INBOX
                                )
                            ).first()
                            
                            if inbox_folder:
                                # 이미 할당되어 있는지 확인
                                existing_relation = db.query(MailInFolder).filter(
                                    and_(
                                        MailInFolder.mail_uuid == mail.mail_uuid,
                                        MailInFolder.folder_uuid == inbox_folder.folder_uuid,
                                        MailInFolder.user_uuid == recipient_mail_user.user_uuid
                                    )
                                ).first()
                                
                                if not existing_relation:
                                    mail_in_inbox = MailInFolder(
                                        mail_uuid=mail.mail_uuid,
                                        folder_uuid=inbox_folder.folder_uuid,
                                        user_uuid=recipient_mail_user.user_uuid,
                                        is_read=False  # 새 메일은 읽지 않음 상태
                                    )
                                    db.add(mail_in_inbox)
                                    print(f"   ✅ 수신자 {recipient.recipient_email} 받은편지함에 할당: {inbox_folder.folder_uuid}")
                                    fixed_count += 1
                                else:
                                    print(f"   ⚠️ 이미 수신자 {recipient.recipient_email} 받은편지함에 할당됨")
                            else:
                                print(f"   ❌ 수신자 {recipient.recipient_email}의 받은편지함을 찾을 수 없습니다")
                                error_count += 1
                        else:
                            print(f"   ❌ 수신자 MailUser를 찾을 수 없습니다: {recipient.recipient_email}")
                            error_count += 1
                
                else:
                    print(f"   ⚠️ 알 수 없는 메일 상태: {mail.status}")
                    error_count += 1
                
            except Exception as e:
                print(f"   ❌ 메일 처리 중 오류: {str(e)}")
                error_count += 1
                continue
        
        # 변경사항 커밋
        db.commit()
        
        print(f"\n📊 처리 결과:")
        print(f"   ✅ 성공적으로 할당된 메일-폴더 관계: {fixed_count}")
        print(f"   ❌ 오류 발생: {error_count}")
        print(f"   📁 처리된 메일 수: {len(mails_without_folder)}")
        
        # 최종 확인
        final_mails_with_folder = db.query(Mail).join(MailInFolder, Mail.mail_uuid == MailInFolder.mail_uuid).count()
        final_unassigned = total_mails - final_mails_with_folder
        
        print(f"\n🎯 최종 상태:")
        print(f"   📊 전체 메일 수: {total_mails}")
        print(f"   📁 폴더에 할당된 메일 수: {final_mails_with_folder}")
        print(f"   ❌ 여전히 할당되지 않은 메일 수: {final_unassigned}")
        
        if final_unassigned == 0:
            print("🎉 모든 메일이 성공적으로 폴더에 할당되었습니다!")
        else:
            print(f"⚠️ {final_unassigned}개의 메일이 여전히 할당되지 않았습니다.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 스크립트 실행 중 오류 발생: {str(e)}")
        raise
    
    finally:
        db.close()

if __name__ == "__main__":
    fix_mail_folder_assignments()