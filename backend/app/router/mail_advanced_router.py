from fastapi import APIRouter, HTTPException, Depends, Query, Form, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func, text
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import json
import os
import zipfile
import tempfile
from pathlib import Path

from ..database.base import get_db
from ..model.base_model import User
from ..model.mail_model import (
    Mail, MailUser, MailRecipient, MailAttachment, MailFolder, MailInFolder, 
    MailLog
)
# 스키마 import 제거 - 기본 타입 사용
from ..service.auth_service import get_current_user

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 라우터 초기화 - 고급 기능
router = APIRouter(tags=["mail-advanced"])

# 백업 저장 디렉토리
BACKUP_DIR = os.path.join(os.getcwd(), "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)


# ===== 폴더 관리 =====

@router.get("/folders", summary="폴더 목록 조회")
async def get_folders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자의 모든 폴더 조회"""
    try:
        logger.info(f"User {current_user.email} is fetching folders")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 폴더 조회
        folders = db.query(MailFolder).filter(MailFolder.user_id == mail_user.id).all()
        
        # 각 폴더의 메일 개수 계산
        folder_list = []
        for folder in folders:
            mail_count = db.query(MailInFolder).filter(MailInFolder.folder_id == folder.id).count()
            
            folder_list.append({
                "id": folder.id,
                "name": folder.name,
                "folder_type": folder.folder_type,
                "mail_count": mail_count,
                "created_at": folder.created_at
            })
        
        return {"folders": folder_list}
        
    except Exception as e:
        logger.error(f"Error fetching folders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"폴더 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/folders", summary="폴더 생성")
async def create_folder(
    folder_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """새 폴더 생성"""
    try:
        logger.info(f"User {current_user.email} is creating folder: {folder_data.get('name')}")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 폴더명 중복 확인
        existing_folder = db.query(MailFolder).filter(
            MailFolder.user_id == mail_user.id,
            MailFolder.name == folder_data.get('name')
        ).first()
        
        if existing_folder:
            raise HTTPException(status_code=400, detail="폴더명이 이미 존재합니다")
        
        # 새 폴더 생성
        new_folder = MailFolder(
            user_id=mail_user.id,
            name=folder_data.get('name'),
            folder_type=folder_data.get('folder_type', 'custom')
        )
        
        db.add(new_folder)
        db.commit()
        db.refresh(new_folder)
        
        return {
            "id": new_folder.id,
            "name": new_folder.name,
            "folder_type": new_folder.folder_type,
            "mail_count": 0,
            "created_at": new_folder.created_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating folder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"폴더 생성 중 오류가 발생했습니다: {str(e)}")


@router.put("/folders/{folder_id}", summary="폴더 수정")
async def update_folder(
    folder_id: str,
    folder_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """폴더 정보 수정"""
    try:
        logger.info(f"User {current_user.email} is updating folder {folder_id}")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 폴더 조회
        folder = db.query(MailFolder).filter(
            and_(
                MailFolder.id == folder_id,
                MailFolder.user_id == mail_user.id
            )
        ).first()
        
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        
        # 시스템 폴더는 수정 불가
        if folder.folder_type in ['inbox', 'sent', 'drafts', 'trash']:
            raise HTTPException(status_code=400, detail="시스템 폴더는 수정할 수 없습니다")
        
        # 폴더명 중복 확인 (자신 제외)
        if folder_data.get('name') and folder_data.get('name') != folder.name:
            existing_folder = db.query(MailFolder).filter(
                and_(
                    MailFolder.user_id == mail_user.id,
                    MailFolder.name == folder_data.get('name'),
                    MailFolder.id != folder_id
                )
            ).first()
            
            if existing_folder:
                raise HTTPException(status_code=400, detail="이미 존재하는 폴더명입니다")
        
        # 폴더 정보 업데이트
        if folder_data.get('name'):
            folder.name = folder_data.get('name')
        
        folder.updated_at = datetime.utcnow()
        db.commit()
        
        # 메일 개수 계산
        mail_count = db.query(MailInFolder).filter(MailInFolder.folder_id == folder.id).count()
        
        return {
            "id": folder.id,
            "name": folder.name,
            "folder_type": folder.folder_type,
            "mail_count": mail_count,
            "created_at": folder.created_at,
            "updated_at": folder.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating folder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"폴더 수정 중 오류가 발생했습니다: {str(e)}")


@router.delete("/folders/{folder_id}", summary="폴더 삭제")
async def delete_folder(
    folder_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """폴더 삭제"""
    try:
        logger.info(f"User {current_user.email} is deleting folder {folder_id}")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 폴더 조회
        folder = db.query(MailFolder).filter(
            and_(
                MailFolder.id == folder_id,
                MailFolder.user_id == mail_user.id
            )
        ).first()
        
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        
        # 시스템 폴더는 삭제 불가
        if folder.folder_type in ['inbox', 'sent', 'drafts', 'trash']:
            raise HTTPException(status_code=400, detail="시스템 폴더는 삭제할 수 없습니다")
        
        # 폴더 내 메일들을 받은편지함으로 이동
        inbox_folder = db.query(MailFolder).filter(
            and_(
                MailFolder.user_id == mail_user.id,
                MailFolder.folder_type == 'inbox'
            )
        ).first()
        
        if inbox_folder:
            db.query(MailInFolder).filter(
                MailInFolder.folder_id == folder_id
            ).update({"folder_id": inbox_folder.id})
        else:
            # 받은편지함이 없으면 폴더 내 메일 관계 삭제
            db.query(MailInFolder).filter(MailInFolder.folder_id == folder_id).delete()
        
        # 폴더 삭제
        db.delete(folder)
        db.commit()
        
        return {
            "success": True,
            "message": "폴더가 삭제되었습니다.",
            "data": {"folder_id": folder_id}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting folder: {str(e)}")
        return {
            "success": False,
            "message": f"폴더 삭제 중 오류가 발생했습니다: {str(e)}",
            "data": {}
        }


@router.post("/folders/{folder_id}/mails/{mail_id}", summary="메일을 폴더로 이동")
async def move_mail_to_folder(
    folder_id: str,
    mail_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """메일을 특정 폴더로 이동"""
    try:
        logger.info(f"User {current_user.email} is moving mail {mail_id} to folder {folder_id}")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 폴더 조회
        folder = db.query(MailFolder).filter(
            and_(
                MailFolder.id == folder_id,
                MailFolder.user_id == mail_user.id
            )
        ).first()
        
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        
        # 메일 조회
        mail = db.query(Mail).filter(Mail.id == mail_id).first()
        if not mail:
            raise HTTPException(status_code=404, detail="Mail not found")
        
        # 권한 확인
        is_sender = mail.sender_id == mail_user.id
        is_recipient = db.query(MailRecipient).filter(
            and_(
                MailRecipient.mail_id == mail.id,
                MailRecipient.recipient_id == mail_user.id
            )
        ).first() is not None
        
        if not (is_sender or is_recipient):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 기존 폴더 관계 확인
        existing_relation = db.query(MailInFolder).filter(
            MailInFolder.mail_id == mail_id
        ).first()
        
        if existing_relation:
            # 기존 관계 업데이트
            existing_relation.folder_id = folder_id
            existing_relation.moved_at = datetime.utcnow()
        else:
            # 새 관계 생성
            new_relation = MailInFolder(
                mail_id=mail_id,
                folder_id=folder_id,
                moved_at=datetime.utcnow()
            )
            db.add(new_relation)
        
        db.commit()
        
        # 로그 기록
        log_entry = MailLog(
            mail_id=mail.id,
            user_id=current_user.id,
            action=f"moved_to_folder_{folder.name}",
            timestamp=datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()
        
        return {
            "success": True,
            "message": f"메일이 '{folder.name}' 폴더로 이동되었습니다.",
            "data": {
                "mail_id": mail_id,
                "folder_id": folder_id,
                "folder_name": folder.name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error moving mail to folder: {str(e)}")
        return {
            "success": False,
            "message": f"메일 이동 중 오류가 발생했습니다: {str(e)}",
            "data": {}
        }





# ===== 백업 및 복원 =====

@router.post("/backup", summary="메일 백업")
async def backup_mails(
    include_attachments: bool = Query(False, description="첨부파일 포함 여부"),
    date_from: Optional[datetime] = Query(None, description="백업 시작 날짜"),
    date_to: Optional[datetime] = Query(None, description="백업 종료 날짜"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자 메일 백업"""
    try:
        logger.info(f"User {current_user.email} is creating mail backup")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 백업할 메일 조회
        query = db.query(Mail).filter(
            or_(
                Mail.sender_id == mail_user.id,
                Mail.id.in_(
                    db.query(MailRecipient.mail_id).filter(
                        MailRecipient.recipient_id == mail_user.id
                    )
                )
            )
        )
        
        # 날짜 필터 적용
        if date_from:
            query = query.filter(Mail.created_at >= date_from)
        if date_to:
            end_date = date_to + timedelta(days=1)
            query = query.filter(Mail.created_at < end_date)
        
        mails = query.all()
        
        # 백업 파일 생성
        backup_filename = f"mail_backup_{current_user.email}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 메일 데이터 JSON 파일 생성
            mail_data = []
            
            for mail in mails:
                # 발신자 정보
                sender = db.query(MailUser).filter(MailUser.id == mail.sender_id).first()
                
                # 수신자 정보
                recipients = db.query(MailRecipient).filter(MailRecipient.mail_id == mail.id).all()
                
                # 첨부파일 정보
                attachments = db.query(MailAttachment).filter(MailAttachment.mail_id == mail.id).all()
                
                mail_info = {
                    "id": mail.id,
                    "subject": mail.subject,
                    "content": mail.body_text,
                    "sender_email": sender.email if sender else None,
                    "recipients": [
                        {
                            "email": r.recipient.email,
                            "type": r.recipient_type,
                            "name": r.recipient.email  # MailUser 모델에 name 필드가 없으므로 email 사용
                        } for r in recipients
                    ],
                    "status": mail.status,
                    "priority": mail.priority,
                    "created_at": mail.created_at.isoformat() if mail.created_at else None,
                    "sent_at": mail.sent_at.isoformat() if mail.sent_at else None,
                    "attachments": [
                        {
                            "filename": a.filename,
                            "file_path": a.file_path,
                            "file_size": a.file_size,
                            "content_type": a.content_type
                        } for a in attachments
                    ]
                }
                
                mail_data.append(mail_info)
                
                # 첨부파일 포함
                if include_attachments:
                    for attachment in attachments:
                        if attachment.file_path and os.path.exists(attachment.file_path):
                            # ZIP 내 경로 설정
                            zip_path = f"attachments/{mail.id}/{attachment.filename}"
                            zipf.write(attachment.file_path, zip_path)
            
            # 메일 데이터를 JSON 파일로 추가
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            try:
                json.dump(mail_data, temp_file, indent=2, ensure_ascii=False, default=str)
                temp_file.flush()
                temp_file.close()  # 파일을 명시적으로 닫음
                zipf.write(temp_file.name, "mails.json")
            finally:
                # 임시 파일 정리
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
        
        # 백업 파일 크기 계산
        backup_size = os.path.getsize(backup_path)
        
        return {
            "success": True,
            "message": "메일 백업이 완료되었습니다.",
            "data": {
                "backup_filename": backup_filename,
                "backup_path": backup_path,
                "mail_count": len(mails),
                "backup_size": backup_size,
                "include_attachments": include_attachments,
                "created_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating mail backup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메일 백업 중 오류가 발생했습니다: {str(e)}")


@router.get("/backup/{backup_filename}", summary="백업 파일 다운로드")
async def download_backup(
    backup_filename: str,
    current_user: User = Depends(get_current_user)
):
    """백업 파일 다운로드"""
    try:
        logger.info(f"User {current_user.email} is downloading backup: {backup_filename}")
        
        # 파일명 검증 (보안)
        if not backup_filename.startswith(f"mail_backup_{current_user.email}_"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=404, detail="Backup file not found")
        
        return FileResponse(
            path=backup_path,
            filename=backup_filename,
            media_type='application/zip'
        )
        
    except Exception as e:
        logger.error(f"Error downloading backup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"백업 파일 다운로드 중 오류가 발생했습니다: {str(e)}")


@router.post("/restore", summary="메일 복원")
async def restore_mails(
    backup_file: UploadFile = File(..., description="백업 파일"),
    overwrite_existing: bool = Form(False, description="기존 메일 덮어쓰기 여부"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """백업 파일로부터 메일 복원"""
    try:
        logger.info(f"User {current_user.email} is restoring mails from backup")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            content = await backup_file.read()
            temp_file.write(content)
            temp_file.flush()
            
            # ZIP 파일 읽기
            with zipfile.ZipFile(temp_file.name, 'r') as zipf:
                # mails.json 파일 읽기
                if 'mails.json' not in zipf.namelist():
                    raise HTTPException(status_code=400, detail="Invalid backup file format")
                
                with zipf.open('mails.json') as json_file:
                    mail_data = json.load(json_file)
                
                restored_count = 0
                skipped_count = 0
                
                for mail_info in mail_data:
                    try:
                        # 기존 메일 확인
                        existing_mail = db.query(Mail).filter(Mail.id == mail_info['id']).first()
                        
                        if existing_mail and not overwrite_existing:
                            skipped_count += 1
                            continue
                        
                        # 메일 복원 또는 생성
                        if existing_mail:
                            # 기존 메일 업데이트
                            existing_mail.subject = mail_info['subject']
                            existing_mail.body_text = mail_info['content']
                            existing_mail.status = mail_info['status']
                            existing_mail.priority = mail_info['priority']
                            if mail_info['sent_at']:
                                existing_mail.sent_at = datetime.fromisoformat(mail_info['sent_at'])
                            if mail_info['read_at']:
                                existing_mail.read_at = datetime.fromisoformat(mail_info['read_at'])
                        else:
                            # 새 메일 생성
                            new_mail = Mail(
                                id=mail_info['id'],
                                subject=mail_info['subject'],
                                content=mail_info['content'],
                                sender_id=mail_user.id,  # 현재 사용자로 설정
                                status=mail_info['status'],
                                priority=mail_info['priority'],
                                created_at=datetime.fromisoformat(mail_info['created_at']) if mail_info['created_at'] else datetime.utcnow(),
                                sent_at=datetime.fromisoformat(mail_info['sent_at']) if mail_info['sent_at'] else None,
                                read_at=datetime.fromisoformat(mail_info['read_at']) if mail_info['read_at'] else None
                            )
                            db.add(new_mail)
                        
                        # 수신자 정보 복원
                        if not existing_mail:
                            for recipient_info in mail_info['recipients']:
                                recipient = MailRecipient(
                                    mail_id=mail_info['id'],
                                    email=recipient_info['email'],
                                    type=recipient_info['type'],
                                    name=recipient_info.get('name')
                                )
                                db.add(recipient)
                        
                        restored_count += 1
                        
                    except Exception as mail_error:
                        logger.error(f"Error restoring mail {mail_info['id']}: {str(mail_error)}")
                        continue
                
                db.commit()
            
            # 임시 파일 삭제
            os.unlink(temp_file.name)
        
        return {
            "success": True,
            "message": f"메일 복원이 완료되었습니다. (복원: {restored_count}개, 건너뜀: {skipped_count}개)",
            "data": {
                "restored_count": restored_count,
                "skipped_count": skipped_count,
                "overwrite_existing": overwrite_existing
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error restoring mails: {str(e)}")
        return {
            "success": False,
            "message": f"메일 복원 중 오류가 발생했습니다: {str(e)}",
            "data": {}
        }


@router.get("/analytics", summary="메일 분석")
async def get_mail_analytics(
    period: str = Query("month", description="분석 기간 (week, month, year)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """메일 사용 분석"""
    try:
        logger.info(f"User {current_user.email} is fetching mail analytics for period: {period}")
        
        # 메일 사용자 조회
        mail_user = db.query(MailUser).filter(MailUser.user_id == current_user.id).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="Mail user not found")
        
        # 기간 설정
        now = datetime.utcnow()
        if period == "week":
            start_date = now - timedelta(weeks=1)
        elif period == "month":
            start_date = now - timedelta(days=30)
        elif period == "year":
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=30)  # 기본값
        
        # 보낸 메일 통계
        sent_mails = db.query(Mail).filter(
            and_(
                Mail.sender_id == mail_user.id,
                Mail.created_at >= start_date,
                Mail.status == 'sent'
            )
        ).all()
        
        # 받은 메일 통계
        received_mails = db.query(Mail).join(
            MailRecipient, Mail.id == MailRecipient.mail_id
        ).filter(
            and_(
                MailRecipient.recipient_id == mail_user.id,
                Mail.created_at >= start_date
            )
        ).all()
        
        # 일별 통계
        daily_stats = {}
        for i in range((now - start_date).days + 1):
            date = start_date + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            daily_stats[date_str] = {
                "sent": 0,
                "received": 0
            }
        
        for mail in sent_mails:
            date_str = mail.created_at.strftime('%Y-%m-%d')
            if date_str in daily_stats:
                daily_stats[date_str]["sent"] += 1
        
        for mail in received_mails:
            date_str = mail.created_at.strftime('%Y-%m-%d')
            if date_str in daily_stats:
                daily_stats[date_str]["received"] += 1
        
        # 우선순위별 통계
        priority_stats = {
            "high": 0,
            "normal": 0,
            "low": 0
        }
        
        all_mails = sent_mails + received_mails
        for mail in all_mails:
            if mail.priority == 'high':
                priority_stats["high"] += 1
            elif mail.priority == 'low':
                priority_stats["low"] += 1
            else:
                priority_stats["normal"] += 1
        
        # 상위 발신자/수신자 통계
        sender_stats = {}
        recipient_stats = {}
        
        for mail in received_mails:
            sender = db.query(MailUser).filter(MailUser.id == mail.sender_id).first()
            if sender:
                sender_email = sender.email
                sender_stats[sender_email] = sender_stats.get(sender_email, 0) + 1
        
        for mail in sent_mails:
            recipients = db.query(MailRecipient).filter(MailRecipient.mail_id == mail.id).all()
            for recipient in recipients:
                recipient_email = recipient.email
                recipient_stats[recipient_email] = recipient_stats.get(recipient_email, 0) + 1
        
        # 상위 5개만 선택
        top_senders = sorted(sender_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        top_recipients = sorted(recipient_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "success": True,
            "message": "메일 분석 조회 성공",
            "data": {
                "period": period,
                "start_date": start_date.isoformat(),
                "end_date": now.isoformat(),
                "summary": {
                    "total_sent": len(sent_mails),
                    "total_received": len(received_mails),
                    "total_mails": len(all_mails)
                },
                "daily_stats": daily_stats,
                "priority_stats": priority_stats,
                "top_senders": [{
                    "email": email,
                    "count": count
                } for email, count in top_senders],
                "top_recipients": [{
                    "email": email,
                    "count": count
                } for email, count in top_recipients]
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching mail analytics: {str(e)}")
        return {
            "success": False,
            "message": f"메일 분석 조회 중 오류가 발생했습니다: {str(e)}",
            "data": {}
        }