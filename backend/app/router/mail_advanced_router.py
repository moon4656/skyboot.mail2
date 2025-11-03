from fastapi import APIRouter, HTTPException, Depends, Query, Form, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func, text
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import re
import logging
import json
import os
import zipfile
import tempfile
import uuid
from pathlib import Path

from ..database.user import get_db
from ..model.user_model import User
from ..model.mail_model import (
    Mail, MailUser, MailRecipient, MailAttachment, MailFolder, MailInFolder, 
    MailLog
)
from ..schemas.mail_schema import FolderListResponse, FolderCreateResponse, FolderCreate, FolderUpdate
from ..service.auth_service import get_current_user
from ..middleware.tenant_middleware import get_current_org_id

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 라우터 초기화 - 고급 기능
router = APIRouter()

# 백업 저장 디렉토리
BACKUP_DIR = os.path.join(os.getcwd(), "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)


# ===== 폴더 관리 =====

@router.get("/folders", response_model=FolderListResponse, summary="폴더 목록 조회")
async def get_folders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id)
) -> FolderListResponse:
    """사용자의 모든 폴더 조회"""
    try:
        logger.info(f"📁 get_folders 시작 - 조직: {current_org_id}, 사용자: {current_user.email}")
        
        # 메일 사용자 조회 (조직별 필터링 추가)
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        
        if not mail_user:
            logger.warning(f"⚠️ 메일 사용자를 찾을 수 없음 - 조직: {current_org_id}, 사용자: {current_user.email}")
            raise HTTPException(status_code=404, detail="조직 내에서 메일 사용자를 찾을 수 없습니다")
        
        # 폴더 조회 (조직별 필터링 추가)
        folders = db.query(MailFolder).filter(
            MailFolder.user_uuid == mail_user.user_uuid,    
            MailFolder.org_id == current_org_id
        ).all()
        
        # 각 폴더의 메일 개수 계산
        folder_list = []
        for folder in folders:
            mail_count = db.query(MailInFolder).filter(MailInFolder.folder_uuid == folder.folder_uuid).count()
            
            folder_list.append({
                "folder_uuid": folder.folder_uuid,
                "name": folder.name,
                "folder_type": folder.folder_type,
                "mail_count": mail_count,
                "created_at": folder.created_at
            })
        
        logger.info(f"✅ get_folders 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 폴더 수: {len(folder_list)}")
        
        return FolderListResponse(folders=folder_list)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ get_folders 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"폴더 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/folders", response_model=FolderCreateResponse, summary="폴더 생성")
async def create_folder(
    folder_data: FolderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id)
) -> FolderCreateResponse:
    """새 폴더 생성"""
    try:
        logger.info(f"📁 create_folder 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 폴더명: {folder_data.name}")
        
        # 메일 사용자 조회 (조직별 필터링 추가)
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,                                                                                   
            MailUser.org_id == current_org_id
        ).first()
        
        if not mail_user:
            logger.warning(f"⚠️ 메일 사용자를 찾을 수 없음 - 조직: {current_org_id}, 사용자: {current_user.email}")
            raise HTTPException(status_code=404, detail="조직 내에서 메일 사용자를 찾을 수 없습니다")
        
        # 폴더명 중복 확인 (조직별 필터링 추가)
        existing_folder = db.query(MailFolder).filter(
            MailFolder.user_uuid == mail_user.user_uuid,
            MailFolder.org_id == current_org_id,
            MailFolder.name == folder_data.name
        ).first()
        
        if existing_folder:
            raise HTTPException(status_code=400, detail="폴더명이 이미 존재합니다")
        
        # UUID 생성
        folder_uuid = str(uuid.uuid4())

        # parent_id 유효성 검증 (같은 사용자/조직의 기존 폴더여야 함)
        parent_id_validated = None
        if folder_data.parent_id is not None:
            parent_folder = db.query(MailFolder).filter(
                and_(
                    MailFolder.id == folder_data.parent_id,
                    MailFolder.user_uuid == mail_user.user_uuid,
                    MailFolder.org_id == current_org_id
                )
            ).first()
            if not parent_folder:
                # 상위 폴더가 유효하지 않으면 최상위 폴더로 생성 (parent_id=None)
                logger.warning(
                    f"⚠️ 상위 폴더를 찾을 수 없음 - 조직: {current_org_id}, 사용자: {current_user.email}, parent_id: {folder_data.parent_id}. 최상위로 생성합니다"
                )
                parent_id_validated = None
            else:
                parent_id_validated = parent_folder.id
        
        # 새 폴더 생성 (조직 ID 추가)
        new_folder = MailFolder(
            folder_uuid=folder_uuid,
            user_uuid=mail_user.user_uuid,
            org_id=current_org_id,
            name=folder_data.name,
            folder_type=folder_data.folder_type,
            parent_id=parent_id_validated  # 검증된 parent_id만 설정
        )
        
        db.add(new_folder)
        db.commit()
        db.refresh(new_folder)
        
        logger.info(f"✅ create_folder 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 폴더명: {new_folder.name}, 폴더 UUID: {new_folder.folder_uuid}")
        
        return FolderCreateResponse(
            id=new_folder.id,
            folder_uuid=new_folder.folder_uuid,
            name=new_folder.name,
            folder_type=new_folder.folder_type,
            mail_count=0,
            created_at=new_folder.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ create_folder 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 폴더명: {folder_data.name}, 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"폴더 생성 중 오류가 발생했습니다: {str(e)}")


@router.put("/folders/{folder_uuid}", response_model=None, summary="폴더 수정")
async def update_folder(
    folder_uuid: str,
    folder_data: FolderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    current_org_id: str = Depends(get_current_org_id)
) -> dict:
    """폴더 정보 수정"""
    try:
        logger.info(f"📁 update_folder 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 폴더 UUID: {folder_uuid}")
        
        # 메일 사용자 조회 (조직별 필터링 추가)
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        
        if not mail_user:
            logger.warning(f"⚠️ 메일 사용자를 찾을 수 없음 - 조직: {current_org_id}, 사용자: {current_user.email}")
            raise HTTPException(status_code=404, detail="조직 내에서 메일 사용자를 찾을 수 없습니다")
        
        # 폴더 조회 (조직별 필터링 추가)
        folder = db.query(MailFolder).filter(
            and_(
                MailFolder.folder_uuid == folder_uuid,
                MailFolder.user_uuid == mail_user.user_uuid,
                MailFolder.org_id == current_org_id
            )
        ).first()
        
        if not folder:
            raise HTTPException(status_code=404, detail="폴더를 찾을 수 없습니다")
        
        # 시스템 폴더는 수정 불가
        if folder.folder_type in ['inbox', 'sent', 'drafts', 'trash']:
            raise HTTPException(status_code=400, detail="시스템 폴더는 수정할 수 없습니다")
        
        # 폴더명 중복 확인 (자신 제외, 조직별 필터링 추가)
        if folder_data.name and folder_data.name != folder.name:
            existing_folder = db.query(MailFolder).filter(
                and_(
                    MailFolder.user_uuid == mail_user.user_uuid,
                    MailFolder.org_id == current_org_id,
                    MailFolder.name == folder_data.name,
                    MailFolder.folder_uuid != folder_uuid
                )
            ).first()
            
            if existing_folder:
                raise HTTPException(status_code=400, detail="이미 존재하는 폴더명입니다")
        
        # 폴더 정보 업데이트
        if folder_data.name:
            folder.name = folder_data.name
        if folder_data.folder_type:
            folder.folder_type = folder_data.folder_type
        if folder_data.parent_id is not None:
            # 자기 자신을 부모로 설정 방지
            if folder_data.parent_id == folder.id:
                raise HTTPException(status_code=400, detail="자기 자신을 상위 폴더로 설정할 수 없습니다")

            # 같은 사용자/조직의 유효한 상위 폴더인지 검증
            parent_folder = db.query(MailFolder).filter(
                and_(
                    MailFolder.id == folder_data.parent_id,
                    MailFolder.user_uuid == mail_user.user_uuid,
                    MailFolder.org_id == current_org_id
                )
            ).first()

            if not parent_folder:
                # 유효하지 않으면 최상위로 변경
                logger.warning(
                    f"⚠️ 상위 폴더를 찾을 수 없음 - 조직: {current_org_id}, 사용자: {current_user.email}, parent_id: {folder_data.parent_id}. 최상위로 변경합니다"
                )
                folder.parent_id = None
            else:
                folder.parent_id = parent_folder.id
        
        folder.updated_at = datetime.utcnow()
        db.commit()
        
        # 메일 개수 계산
        mail_count = db.query(MailInFolder).filter(MailInFolder.folder_uuid == folder.folder_uuid).count()
        
        logger.info(f"✅ update_folder 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 폴더 UUID: {folder.folder_uuid}, 폴더명: {folder.name}")
        
        return {
            "folder_uuid": folder.folder_uuid,
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
        logger.error(f"❌ update_folder 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 폴더 UUID: {folder_uuid}, 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"폴더 수정 중 오류가 발생했습니다: {str(e)}")


@router.delete("/folders/{folder_uuid}", response_model=None, summary="폴더 삭제")
async def delete_folder(
    folder_uuid: str,
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> dict:
    """폴더 삭제"""
    try:
        logger.info(f"🗑️ delete_folder 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 폴더 UUID: {folder_uuid}")
        
        # 메일 사용자 조회 (조직별 필터링 추가)
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        
        if not mail_user:
            logger.warning(f"⚠️ 메일 사용자를 찾을 수 없음 - 조직: {current_org_id}, 사용자: {current_user.email}")
            raise HTTPException(status_code=404, detail="조직 내에서 메일 사용자를 찾을 수 없습니다")
        
        # 폴더 조회 (조직별 필터링 추가)
        folder = db.query(MailFolder).filter(
            and_(
                MailFolder.folder_uuid == folder_uuid,
                MailFolder.user_uuid == mail_user.user_uuid,
                MailFolder.org_id == current_org_id
            )
        ).first()
        
        if not folder:
            raise HTTPException(status_code=404, detail="폴더를 찾을 수 없습니다")
        
        # 시스템 폴더는 삭제 불가
        if folder.folder_type in ['inbox', 'sent', 'drafts', 'trash']:
            raise HTTPException(status_code=400, detail="시스템 폴더는 삭제할 수 없습니다")
        
        # 폴더 내 메일들을 받은편지함으로 이동 (조직별 필터링 추가)
        inbox_folder = db.query(MailFolder).filter(
            and_(
                MailFolder.user_uuid == mail_user.user_uuid,
                MailFolder.org_id == current_org_id,
                MailFolder.folder_type == 'inbox'
            )
        ).first()
        
        if inbox_folder:
            db.query(MailInFolder).filter(
                MailInFolder.folder_uuid == folder.folder_uuid
            ).update({"folder_uuid": inbox_folder.folder_uuid})
        else:
            # 받은편지함이 없으면 폴더 내 메일 관계 삭제
            db.query(MailInFolder).filter(
                and_(
                    MailInFolder.folder_uuid == folder.folder_uuid,
                    MailInFolder.user_uuid == mail_user.user_uuid
                )
            ).delete()
        
        # 폴더 삭제
        db.delete(folder)
        db.commit()
        
        logger.info(f"✅ delete_folder 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 폴더 UUID: {folder_uuid}, 폴더명: {folder.name}")
        
        return {
            "success": True,
            "message": "폴더가 삭제되었습니다.",
            "data": {"folder_uuid": folder_uuid}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ delete_folder 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 폴더 UUID: {folder_uuid}, 에러: {str(e)}")
        return {
            "success": False,
            "message": f"폴더 삭제 중 오류가 발생했습니다: {str(e)}",
            "data": {}
        }


@router.post("/folders/{folder_uuid}/mails/{mail_uuid}", response_model=None, summary="메일을 폴더로 이동")
async def move_mail_to_folder(
    folder_uuid: str,
    mail_uuid: str,
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> dict:
    """메일을 특정 폴더로 이동"""
    try:
        logger.info(f"📁 move_mail_to_folder 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일 UUID: {mail_uuid}, 폴더 UUID: {folder_uuid}")
        
        # 메일 사용자 조회 (조직별 필터링 추가)
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        
        if not mail_user:
            logger.warning(f"⚠️ 메일 사용자를 찾을 수 없음 - 조직: {current_org_id}, 사용자: {current_user.email}")
            raise HTTPException(status_code=404, detail="조직 내에서 메일 사용자를 찾을 수 없습니다")
        
        # 폴더 조회 (조직별 필터링 추가)
        folder = db.query(MailFolder).filter(
            and_(
                MailFolder.folder_uuid == folder_uuid,
                MailFolder.user_uuid == mail_user.user_uuid,
                MailFolder.org_id == current_org_id
            )
        ).first()
        
        if not folder:
            raise HTTPException(status_code=404, detail="폴더를 찾을 수 없습니다")
        
        # 메일 조회 (조직별 필터링 추가)
        mail = db.query(Mail).filter(
            Mail.mail_uuid == mail_uuid,
            Mail.org_id == current_org_id
        ).first()
        
        if not mail:
            raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다")
        
        # 권한 확인
        is_sender = mail.sender_uuid == mail_user.user_uuid
        is_recipient = db.query(MailRecipient).filter(
            and_(
                MailRecipient.mail_uuid == mail.mail_uuid,
                MailRecipient.recipient_uuid == mail_user.user_uuid
            )
        ).first() is not None
        
        if not (is_sender or is_recipient):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 기존 폴더 관계 확인
        existing_relation = db.query(MailInFolder).filter(
            MailInFolder.mail_uuid == mail.mail_uuid,
            MailInFolder.user_uuid == mail_user.user_uuid
        ).first()
        
        if existing_relation:
            # 기존 관계 업데이트
            existing_relation.folder_uuid = folder.folder_uuid
        else:
            # 새 관계 생성
            new_relation = MailInFolder(
                mail_uuid=mail.mail_uuid,
                folder_uuid=folder.folder_uuid,
                user_uuid=mail_user.user_uuid
            )
            db.add(new_relation)
        
        db.commit()
        
        # 로그 기록 (조직/메일사용자 정보 포함)
        log_entry = MailLog(
            action="moved_to_folder",
            details=f"메일을 '{folder.name}' 폴더로 이동",
            mail_uuid=mail.mail_uuid,
            user_uuid=mail_user.user_uuid,
            org_id=current_org_id,
            ip_address=None,  # TODO: 실제 IP 주소 추가
            user_agent=None   # TODO: 실제 User-Agent 추가
        )
        db.add(log_entry)
        db.commit()
        
        logger.info(f"✅ move_mail_to_folder 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일 UUID: {mail_uuid}, 폴더: {folder.name}")
        
        return {
            "success": True,
            "message": f"메일이 '{folder.name}' 폴더로 이동되었습니다.",
            "data": {
                "mail_uuid": mail.mail_uuid,
                "folder_uuid": folder.folder_uuid,
                "folder_name": folder.name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ move_mail_to_folder 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일 ID: {mail.mail_uuid}, 폴더 ID: {folder_uuid}, 에러: {str(e)}")
        return {
            "success": False,
            "message": f"메일 이동 중 오류가 발생했습니다: {str(e)}",
            "data": {}
        }

# ===== 백업 및 복원 =====

@router.post("/backup", response_model=None, summary="메일 백업")
async def backup_mails(
    include_attachments: bool = Query(False, description="첨부파일 포함 여부"),
    date_from: Optional[str] = Query(None, description="백업 시작 날짜 (YYYYMMDD, YYYY-MM-DD, ISO8601 지원)"),
    date_to: Optional[str] = Query(None, description="백업 종료 날짜 (YYYYMMDD, YYYY-MM-DD, ISO8601 지원)"),
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> dict:
    """사용자 메일 백업"""
    try:
        logger.info(f"💾 backup_mails 시작 - 조직: {current_org_id}, 사용자: {current_user.email}")

        # 날짜 파라미터 파싱 함수
        def _parse_date_param(date_str: Optional[str], end_of_day: bool = False) -> Optional[datetime]:
            """문자열 날짜를 UTC 인식 datetime으로 변환합니다."""
            if not date_str:
                return None
            s = date_str.strip()
            try:
                # YYYYMMDD
                if re.fullmatch(r"\d{8}", s):
                    year = int(s[0:4]); month = int(s[4:6]); day = int(s[6:8])
                    dt = datetime(year, month, day, tzinfo=timezone.utc)
                # YYYY-MM-DD
                elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
                    dt = datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                else:
                    # ISO8601 등 일반 포맷 시도
                    dt = datetime.fromisoformat(s)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    else:
                        dt = dt.astimezone(timezone.utc)
                if end_of_day:
                    # 종료일의 하루 끝을 포함하기 위해 다음날 00:00로 설정
                    dt = dt + timedelta(days=1)
                return dt
            except Exception:
                return None
        
        # 메일 사용자 조회 (조직별 필터링 추가)
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        
        if not mail_user:
            logger.warning(f"⚠️ 메일 사용자를 찾을 수 없음 - 조직: {current_org_id}, 사용자: {current_user.email}")
            raise HTTPException(status_code=404, detail="조직 내에서 메일 사용자를 찾을 수 없습니다")
        
        # 백업할 메일 조회 (조직별 필터링 추가)
        query = db.query(Mail).filter(
            and_(
                Mail.org_id == current_org_id,
                or_(
                    Mail.sender_uuid == mail_user.user_uuid,
                    Mail.mail_uuid.in_(
                        db.query(MailRecipient.mail_uuid).filter(
                            MailRecipient.recipient_email == mail_user.email
                        )
                    )
                )
            )
        )
        
        # 날짜 필터 파싱 및 적용 (sent_at 우선, 없으면 created_at 기준)
        start_dt = _parse_date_param(date_from, end_of_day=False)
        end_dt = _parse_date_param(date_to, end_of_day=True)

        if start_dt:
            query = query.filter(
                or_(
                    and_(Mail.sent_at.isnot(None), Mail.sent_at >= start_dt),
                    and_(Mail.sent_at.is_(None), Mail.created_at >= start_dt)
                )
            )
        if end_dt:
            query = query.filter(
                or_(
                    and_(Mail.sent_at.isnot(None), Mail.sent_at < end_dt),
                    and_(Mail.sent_at.is_(None), Mail.created_at < end_dt)
                )
            )
        
        mails = query.all()
        
        # 백업 파일 생성
        backup_filename = f"mail_backup_{current_user.email}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 메일 데이터 JSON 파일 생성
            mail_data = []
            
            for mail in mails:
                # 발신자 정보
                sender = db.query(MailUser).filter(MailUser.user_uuid == mail.sender_uuid).first()
                
                # 수신자 정보
                recipients = db.query(MailRecipient).filter(MailRecipient.mail_uuid == mail.mail_uuid).all()
                
                # 첨부파일 정보
                attachments = db.query(MailAttachment).filter(MailAttachment.mail_uuid == mail.mail_uuid).all()
                
                mail_info = {
                    "id": mail.mail_uuid,
                    "subject": mail.subject,
                    "content": mail.body_text,
                    "sender_email": sender.email if sender else None,
                    "recipients": [
                        {
                            "email": r.recipient_email,
                            "type": r.recipient_type,
                            "name": r.recipient_email  # MailUser 모델에 name 필드가 없으므로 email 사용
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
                            zip_path = f"attachments/{mail.mail_uuid}/{attachment.filename}"
                            zipf.write(attachment.file_path, zip_path)
            
            # 메일 데이터를 JSON 파일로 추가 (UTF-8 인코딩 명시)
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
            try:
                json.dump(mail_data, temp_file, indent=2, ensure_ascii=False, default=str)
                temp_file.flush()
                temp_file.close()  # 파일을 명시적으로 닫음
                zipf.write(temp_file.name, "mails.json")
                logger.info(f"📄 JSON 파일 생성 완료 (UTF-8 인코딩): mails.json")
            finally:
                # 임시 파일 정리
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
        
        # 백업 파일 크기 계산
        backup_size = os.path.getsize(backup_path)
        
        logger.info(f"✅ backup_mails 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 메일 수: {len(mails)}, 파일 크기: {backup_size}, 범위: {date_from}~{date_to}")
        
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
        logger.error(f"❌ backup_mails 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메일 백업 중 오류가 발생했습니다: {str(e)}")


@router.get("/backup/{backup_filename}", response_model=None, summary="백업 파일 다운로드")
async def download_backup(
    backup_filename: str,
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id)
) -> FileResponse:
    """백업 파일 다운로드"""
    try:
        logger.info(f"📥 download_backup 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 파일: {backup_filename}")

        # 파일명 정규화: 앞뒤 공백 및 따옴표 제거, 경로 분리자 제거
        normalized_name = backup_filename.strip().strip('"').strip("'")
        normalized_name = os.path.basename(normalized_name)

        if normalized_name != backup_filename:
            logger.info(
                f"ℹ️ 파일명 정규화 적용 - 원본: {backup_filename}, 정규화: {normalized_name}"
            )

        # 파일명 검증 (사용자 이메일 기반 프리픽스)
        expected_prefix = f"mail_backup_{current_user.email}_"
        if not normalized_name.startswith(expected_prefix):
            logger.warning(
                f"⚠️ 백업 파일 접근 거부 - 조직: {current_org_id}, 사용자: {current_user.email}, 파일: {normalized_name}"
            )
            raise HTTPException(status_code=403, detail="접근이 거부되었습니다")

        # 경로 생성 및 디렉터리 탈출 방지
        backup_path = os.path.join(BACKUP_DIR, normalized_name)
        backup_dir_real = Path(BACKUP_DIR).resolve()
        backup_path_real = Path(backup_path).resolve()
        if backup_dir_real not in backup_path_real.parents and backup_path_real != backup_dir_real:
            logger.warning(
                f"⚠️ 경로 탈출 시도 차단 - 요청 경로: {backup_path_real}, 허용 경로: {backup_dir_real}"
            )
            raise HTTPException(status_code=403, detail="잘못된 파일 경로입니다")

        # 파일 존재 확인
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=404, detail="백업 파일을 찾을 수 없습니다")

        logger.info(
            f"✅ download_backup 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 파일: {normalized_name}"
        )

        return FileResponse(
            path=backup_path,
            filename=normalized_name,
            media_type='application/zip'
        )

    except HTTPException:
        # 명시적으로 발생시킨 HTTP 오류는 그대로 전달
        raise
    except Exception as e:
        logger.error(
            f"❌ download_backup 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 파일: {backup_filename}, 에러: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=f"백업 파일 다운로드 중 오류가 발생했습니다: {str(e)}")


@router.post("/restore", response_model=None, summary="메일 복원")
async def restore_mails(
    backup_file: UploadFile = File(..., description="백업 파일"),
    overwrite_existing: bool = Form(False, description="기존 메일 덮어쓰기 여부"),
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> dict:
    """백업 파일로부터 메일 복원"""
    try:
        logger.info(f"📦 restore_mails 시작 - 조직: {current_org_id}, 사용자: {current_user.email}")
        
        # 메일 사용자 조회 (조직별 격리)
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="조직 내에서 메일 사용자를 찾을 수 없습니다")
        
        # 임시 파일로 저장
        temp_file_path = None
        try:
            # 임시 파일 생성 및 백업 파일 내용 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
                content = await backup_file.read()
                temp_file.write(content)
                temp_file.flush()
                temp_file_path = temp_file.name
            
            # ZIP 파일 읽기 (파일 핸들을 완전히 분리)
            mail_data = []  # 기본값을 빈 리스트로 설정
            with zipfile.ZipFile(temp_file_path, 'r') as zipf:
                logger.info(f"📦 ZIP 파일 내용: {zipf.namelist()}")
                
                # mails.json 파일 읽기
                if 'mails.json' not in zipf.namelist():
                    logger.error(f"❌ mails.json 파일이 ZIP에 없습니다. 파일 목록: {zipf.namelist()}")
                    raise HTTPException(status_code=400, detail="Invalid backup file format")
                
                # JSON 파일을 바이트로 읽고 다양한 인코딩으로 디코딩 시도
                json_bytes = zipf.read('mails.json')
                logger.info(f"📄 JSON 파일 크기: {len(json_bytes)} bytes")
                
                # 다양한 인코딩 형식 시도
                encodings = ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr', 'latin-1']
                json_content = None
                
                for encoding in encodings:
                    try:
                        json_content = json_bytes.decode(encoding)
                        logger.info(f"📄 JSON 파일 인코딩 감지: {encoding}")
                        break
                    except UnicodeDecodeError:
                        continue
                
                if json_content is None:
                    logger.error(f"❌ JSON 파일 인코딩을 감지할 수 없습니다")
                    raise HTTPException(status_code=400, detail="JSON 파일 인코딩을 감지할 수 없습니다")
                
                logger.info(f"📄 JSON 내용 길이: {len(json_content)} characters")
                logger.info(f"📄 JSON 내용 미리보기: {json_content[:200]}...")
                
                # JSON 파싱
                try:
                    mail_data = json.loads(json_content)
                    logger.info(f"📊 JSON 파싱 성공 - 데이터 타입: {type(mail_data)}")
                    if isinstance(mail_data, list):
                        logger.info(f"📊 메일 데이터 개수: {len(mail_data)}개")
                        if len(mail_data) > 0:
                            logger.info(f"📧 첫 번째 메일 샘플: {mail_data[0]}")
                    else:
                        logger.warning(f"⚠️ 예상하지 못한 데이터 구조: {type(mail_data)}")
                        logger.warning(f"⚠️ 데이터 내용: {mail_data}")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON 파싱 오류: {str(e)}")
                    logger.error(f"JSON 내용: {json_content[:1000]}")
                    raise HTTPException(status_code=400, detail=f"JSON 파일 형식이 올바르지 않습니다: {str(e)}")
            
            # 현재 사용자의 MailUser 정보 가져오기
            mail_user = db.query(MailUser).filter(
                MailUser.user_uuid == current_user.user_uuid,
                MailUser.org_id == current_org_id
            ).first()
            
            # MailUser가 없으면 자동 생성
            if not mail_user:
                logger.info(f"📧 MailUser가 없어서 자동 생성 중 - 사용자: {current_user.user_uuid}, 조직: {current_org_id}")
                
                mail_user = MailUser(
                    user_uuid=current_user.user_uuid,
                    org_id=current_org_id,
                    email=current_user.email if hasattr(current_user, 'email') else f"user_{current_user.user_uuid}@example.com",
                    password_hash="temp_hash",  # 임시 해시
                    display_name=current_user.email.split('@')[0] if hasattr(current_user, 'email') and '@' in current_user.email else f"user_{current_user.user_uuid[:8]}",
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(mail_user)
                db.flush()  # ID 생성을 위해 flush
                
                logger.info(f"✅ MailUser 자동 생성 완료 - UUID: {mail_user.user_uuid}")
            
            # ZIP 파일이 완전히 닫힌 후 메일 데이터 처리
            restored_count = 0
            skipped_count = 0
            
            logger.info(f"📊 복원할 메일 데이터 개수: {len(mail_data) if mail_data else 0}")
            
            if not mail_data:
                logger.warning(f"⚠️ 메일 데이터가 비어있습니다!")
                return {
                    "success": True,
                    "message": "메일 복원이 완료되었습니다. (복원: 0개, 건너뜀: 0개)",
                    "data": {
                        "restored_count": 0,
                        "skipped_count": 0,
                        "overwrite_existing": overwrite_existing
                    }
                }
            
            for i, mail_info in enumerate(mail_data):
                try:
                    # 백업 파일의 필드명 매핑 (id -> mail_uuid, content -> body_text)
                    mail_uuid = mail_info.get('id') or mail_info.get('mail_uuid')
                    mail_content = mail_info.get('content') or mail_info.get('body_text')
                    
                    # 기존 메일 확인 (조직별 격리)
                    existing_mail = db.query(Mail).filter(
                        Mail.mail_uuid == mail_uuid,
                        Mail.org_id == current_org_id
                    ).first()
                    
                    if existing_mail and not overwrite_existing:
                        logger.info(f"⏭️ 기존 메일 건너뜀: {mail_uuid}")
                        skipped_count += 1
                        continue
                    
                    # 메일 복원 또는 생성
                    if existing_mail:
                        # 기존 메일 업데이트
                        logger.info(f"🔄 기존 메일 업데이트: {mail_uuid}")
                        existing_mail.subject = mail_info['subject']
                        existing_mail.body_text = mail_content
                        existing_mail.status = mail_info.get('status', 'sent')
                        existing_mail.priority = mail_info.get('priority', 'normal')
                        if mail_info.get('sent_at'):
                            existing_mail.sent_at = datetime.fromisoformat(mail_info['sent_at'])
                    else:
                        # 새 메일 생성 (조직 ID 포함)
                        logger.info(f"✨ 새 메일 생성: {mail_uuid}")
                        new_mail = Mail(
                            mail_uuid=mail_uuid,
                            subject=mail_info.get('subject', '제목없음'),
                            body_text=mail_content,
                            sender_uuid=mail_user.user_uuid,  # 현재 사용자로 설정
                            org_id=current_org_id,  # 조직 ID 설정
                            status=mail_info.get('status', 'sent'),
                            priority=mail_info.get('priority', 'normal'),
                            created_at=datetime.fromisoformat(mail_info['created_at']) if mail_info.get('created_at') else datetime.utcnow(),
                            sent_at=datetime.fromisoformat(mail_info['sent_at']) if mail_info.get('sent_at') else None
                        )
                        db.add(new_mail)
                        db.flush()  # 메일을 먼저 저장하여 관계 설정 가능하게 함
                    
                    # 수신자 정보 복원 (새 메일인 경우에만)
                    if not existing_mail and 'recipients' in mail_info:
                        logger.info(f"👥 수신자 정보 복원: {len(mail_info['recipients'])}명")
                        for recipient_info in mail_info['recipients']:
                            recipient = MailRecipient(
                                mail_uuid=mail_uuid,
                                recipient_email=recipient_info['email'],
                                recipient_type=recipient_info['type']
                            )
                            db.add(recipient)
                    
                    restored_count += 1
                    logger.info(f"✅ 메일 복원 완료: {mail_uuid}")
                    
                except Exception as mail_error:
                    logger.error(f"❌ 메일 복원 실패 {mail_info.get('id') or mail_info.get('mail_uuid', 'UUID없음')}: {str(mail_error)}")
                    continue
            
            db.commit()
            
        finally:
            # 임시 파일 정리 (예외 발생 여부와 관계없이 실행)
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.info(f"🗑️ 임시 파일 정리 완료: {temp_file_path}")
                except Exception as cleanup_error:
                    logger.warning(f"⚠️ 임시 파일 정리 실패: {temp_file_path}, 오류: {str(cleanup_error)}")
        
        logger.info(f"✅ restore_mails 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 복원: {restored_count}개, 건너뜀: {skipped_count}개")
        
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
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}"
        error_traceback = traceback.format_exc()
        logger.error(f"❌ restore_mails 오류 - 조직: {current_org_id}, 사용자: {current_user.email}")
        logger.error(f"오류 타입: {type(e).__name__}")
        logger.error(f"오류 메시지: {str(e)}")
        logger.error(f"오류 상세:\n{error_traceback}")
        return {
            "success": False,
            "message": f"메일 복원 중 오류가 발생했습니다: {error_detail}",
            "data": {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": error_traceback
            }
        }


@router.get("/analytics", response_model=None, summary="메일 분석")
async def get_mail_analytics(
    period: str = Query("month", description="분석 기간 (week, month, year)"),
    current_user: User = Depends(get_current_user),
    current_org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
) -> dict:
    """메일 사용 분석"""
    try:
        logger.info(f"📊 get_mail_analytics 시작 - 조직: {current_org_id}, 사용자: {current_user.email}, 기간: {period}")
        
        # 메일 사용자 조회 (조직별 격리)
        mail_user = db.query(MailUser).filter(
            MailUser.user_uuid == current_user.user_uuid,
            MailUser.org_id == current_org_id
        ).first()
        if not mail_user:
            raise HTTPException(status_code=404, detail="조직 내에서 메일 사용자를 찾을 수 없습니다")
        
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
        
        # 보낸 메일 통계 (조직별 격리)
        sent_mails = db.query(Mail).filter(
            and_(
                Mail.sender_uuid == mail_user.user_uuid,
                Mail.org_id == current_org_id,
                Mail.created_at >= start_date,
                Mail.status == 'sent'
            )
        ).all()
        
        # 받은 메일 통계 (조직별 격리)
        received_mails = db.query(Mail).join(
            MailRecipient, Mail.mail_uuid == MailRecipient.mail_uuid
        ).filter(
            and_(
                MailRecipient.recipient_uuid == mail_user.user_uuid,
                Mail.org_id == current_org_id,
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
            sender = db.query(MailUser).filter(MailUser.user_uuid == mail.sender_uuid).first()
            if sender:
                sender_email = sender.email
                sender_stats[sender_email] = sender_stats.get(sender_email, 0) + 1
        
        for mail in sent_mails:
            recipients = db.query(MailRecipient).filter(MailRecipient.mail_uuid == mail.mail_uuid).all()
            for recipient in recipients:
                recipient_email = recipient.recipient_email
                recipient_stats[recipient_email] = recipient_stats.get(recipient_email, 0) + 1
        
        # 상위 5개만 선택
        top_senders = sorted(sender_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        top_recipients = sorted(recipient_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        
        logger.info(f"✅ get_mail_analytics 완료 - 조직: {current_org_id}, 사용자: {current_user.email}, 보낸메일: {len(sent_mails)}개, 받은메일: {len(received_mails)}개")
        
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
        logger.error(f"❌ get_mail_analytics 오류 - 조직: {current_org_id}, 사용자: {current_user.email}, 에러: {str(e)}")
        return {
            "success": False,
            "message": f"메일 분석 조회 중 오류가 발생했습니다: {str(e)}",
            "data": {}
        }