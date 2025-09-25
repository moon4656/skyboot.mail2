from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database.base import get_db
from ..model.user_model import User
from ..model.mail_model import MailUser
from ..service.auth_service import get_current_user
from ..database.mail import init_default_folders
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/setup-mail-account", response_model=None, summary="메일 계정 초기화")
async def setup_mail_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    현재 사용자의 메일 계정을 초기화합니다.
    메일 사용자가 없는 경우 생성하고 기본 폴더를 만듭니다.
    """
    try:
        logger.info(f"사용자 {current_user.email}의 메일 계정 초기화 시작")
        
        # 기존 메일 사용자 확인
        existing_mail_user = db.query(MailUser).filter(MailUser.user_uuid == current_user.user_uuid).first()
        
        if existing_mail_user:
            return {
                "success": True,
                "message": "메일 계정이 이미 설정되어 있습니다.",
                "data": {
                    "mail_user_id": existing_mail_user.user_uuid,
                    "email": existing_mail_user.email
                }
            }
        
        # 새 메일 사용자 생성
        mail_user = MailUser(
            user_id=str(current_user.user_uuid),
            email=current_user.email,
            display_name=current_user.username,
            is_active=True
        )
        
        db.add(mail_user)
        db.commit()
        db.refresh(mail_user)
        
        logger.info(f"새 메일 사용자 생성 완료: {mail_user.email}")
        
        # 기본 폴더 생성
        init_default_folders(db, mail_user.user_uuid)
        
        logger.info(f"사용자 {current_user.email}의 메일 계정 초기화 완료")
        
        return {
            "success": True,
            "message": "메일 계정이 성공적으로 초기화되었습니다.",
            "data": {
                "mail_user_id": mail_user.user_uuid,
                "email": mail_user.email,
                "display_name": mail_user.display_name
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"메일 계정 초기화 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"메일 계정 초기화 중 오류가 발생했습니다: {str(e)}"
        )
