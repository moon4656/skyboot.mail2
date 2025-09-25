#!/usr/bin/env python3
"""
기존 메일들의 폴더 할당 상태 확인 및 수정 스크립트

이 스크립트는 다음 작업을 수행합니다:
1. MailInFolder 관계가 없는 메일들을 찾습니다
2. 메일 상태에 따라 적절한 폴더에 자동 할당합니다
3. 발송된 메일 -> 보낸편지함
4. 임시저장 메일 -> 임시보관함
5. 수신된 메일 -> 받은편지함
"""

import sys
import os
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.base import get_db
from app.model.mail_model import Mail, MailUser, MailRecipient, MailFolder, MailInFolder, MailStatus, FolderType, RecipientType

def check_and_fix_mail_folder_assignments():
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
        mails_with_folder = db.query(Mail).join(MailInFolder).count()
        print(f"📁 폴더에 할당된 메일 수: {mails_with_folder}")
        
        # 3. MailInFolder 관계가 없는 메일들 찾기
        mails_without_folder = db.query(Mail).outerjoin(MailInFolder).filter(
            MailInFolder.mail_id.is_(None)
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
                print(f"\n📧 메일 처리 중: ID={mail.id}, 상태={mail.status}, 제목='{mail.subject[:50]}...'")
                
                # 발신자 정보 조회
                sender = db.query(MailUser).filter(MailUser.user_id == mail.sender_uuid).first()
                if not sender:
                    print(f"   ⚠️ 발신자를 찾을 수 없습니다: sender_uuid={mail.sender_uuid}")
                    error_count += 1
                    continue
                
                # 메일 상태에 따른 폴더 할당
                if mail.status == MailStatus.DRAFT:
                    # 임시저장 메일 -> 임시보관함
                    draft_folder = db.query(MailFolder).filter(
                        and_(
                            MailFolder.user_id == sender.id,
                            MailFolder.folder_type == FolderType.DRAFT
                        )
                    ).first()
                    
                    if draft_folder:
                        mail_in_folder = MailInFolder(
                            mail_id=mail.id,
                            folder_id=draft_folder.id
                        )
                        db.add(mail_in_folder)
                        print(f"   ✅ 임시보관함에 할당: 폴더 ID={draft_folder.id}")
                        fixed_count += 1
                    else:
                        print(f"   ❌ 임시보관함을 찾을 수 없습니다: user_id={sender.id}")
                        error_count += 1
                
                elif mail.status == MailStatus.SENT:
                    # 발송된 메일 처리
                    
                    # 1. 발신자의 보낸편지함에 할당
                    sent_folder = db.query(MailFolder).filter(
                        and_(
                            MailFolder.user_id == sender.id,
                            MailFolder.folder_type == FolderType.SENT
                        )
                    ).first()
                    
                    if sent_folder:
                        # 이미 할당되어 있는지 확인
                        existing_relation = db.query(MailInFolder).filter(
                            and_(
                                MailInFolder.mail_id == mail.id,
                                MailInFolder.folder_id == sent_folder.id
                            )
                        ).first()
                        
                        if not existing_relation:
                            mail_in_folder = MailInFolder(
                                mail_id=mail.id,
                                folder_id=sent_folder.id
                            )
                            db.add(mail_in_folder)
                            print(f"   ✅ 발신자 보낸편지함에 할당: 폴더 ID={sent_folder.id}")
                            fixed_count += 1
                    else:
                        print(f"   ❌ 발신자 보낸편지함을 찾을 수 없습니다: user_id={sender.id}")
                        error_count += 1
                    
                    # 2. 수신자들의 받은편지함에 할당
                    recipients = db.query(MailRecipient).filter(MailRecipient.mail_id == mail.id).all()
                    
                    for recipient in recipients:
                        recipient_user = recipient.recipient
                        if recipient_user and recipient_user.is_active:
                            inbox_folder = db.query(MailFolder).filter(
                                and_(
                                    MailFolder.user_id == recipient_user.id,
                                    MailFolder.folder_type == FolderType.INBOX
                                )
                            ).first()
                            
                            if inbox_folder:
                                # 이미 할당되어 있는지 확인
                                existing_relation = db.query(MailInFolder).filter(
                                    and_(
                                        MailInFolder.mail_id == mail.id,
                                        MailInFolder.folder_id == inbox_folder.id
                                    )
                                ).first()
                                
                                if not existing_relation:
                                    mail_in_inbox = MailInFolder(
                                        mail_id=mail.id,
                                        folder_id=inbox_folder.id
                                    )
                                    db.add(mail_in_inbox)
                                    print(f"   ✅ 수신자 {recipient_user.email} 받은편지함에 할당: 폴더 ID={inbox_folder.id}")
                                    fixed_count += 1
                            else:
                                print(f"   ❌ 수신자 {recipient_user.email}의 받은편지함을 찾을 수 없습니다")
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
        final_mails_with_folder = db.query(Mail).join(MailInFolder).count()
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

def show_folder_statistics():
    """폴더별 메일 통계를 보여줍니다."""
    
    print("\n📊 폴더별 메일 통계:")
    print("=" * 60)
    
    db = next(get_db())
    
    try:
        # 모든 사용자의 폴더 조회
        folders = db.query(MailFolder).all()
        
        for folder in folders:
            mail_count = db.query(MailInFolder).filter(MailInFolder.folder_id == folder.id).count()
            user = db.query(MailUser).filter(MailUser.user_id == folder.user_id).first()
            user_email = user.email if user else "Unknown"
            
            print(f"📁 {folder.name} ({folder.folder_type}) - {user_email}: {mail_count}개 메일")
    
    except Exception as e:
        print(f"❌ 통계 조회 중 오류: {str(e)}")
    
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 메일 폴더 할당 상태 확인 및 수정 스크립트")
    print("=" * 60)
    
    # 1. 현재 상태 확인
    show_folder_statistics()
    
    # 2. 폴더 할당 수정
    check_and_fix_mail_folder_assignments()
    
    # 3. 수정 후 상태 확인
    show_folder_statistics()
    
    print("\n✅ 스크립트 실행 완료!")
