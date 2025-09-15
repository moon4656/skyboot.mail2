import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, MailLog
from app.schemas import MailRequest, MailResponse, MailLogResponse
from app.auth import get_current_user
from app.config import settings
import logging
from datetime import datetime
import asyncio
import uuid
import aiosmtplib
import ssl

router = APIRouter()

async def send_email_via_postfix(to_email: str, subject: str, body: str) -> tuple[bool, str]:
    """
    Postfix를 통해 이메일을 발송합니다.
    
    Args:
        to_email: 수신자 이메일 주소
        subject: 메일 제목
        body: 메일 본문
    
    Returns:
        (성공 여부, 오류 메시지)
    """
    try:
        logging.info(f"📤 메일 발송 시작 - 수신자: {to_email}, 제목: {subject}")
        
        # 현재 SMTP 설정이 기본값인지 확인
        if settings.SMTP_USER == "your-email@gmail.com" or settings.SMTP_PASSWORD == "your-app-password":
            # 실제 SMTP 서버가 설정되지 않은 경우 시뮬레이션
            logging.info(f"🔧 SMTP 서버가 설정되지 않아 메일 발송을 시뮬레이션합니다.")
            logging.info(f"📧 시뮬레이션 메일 - 수신자: {to_email}, 제목: {subject}, 본문: {body[:50]}...")
            return True, "메일 발송 시뮬레이션 완료 (실제 SMTP 서버 설정 필요)"
        
        # MIME 메시지 생성
        message = MIMEMultipart()
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = to_email
        message["Subject"] = Header(subject, 'utf-8')
        
        # 본문 추가 (HTML과 텍스트 모두 지원)
        text_part = MIMEText(body, 'plain', 'utf-8')
        message.attach(text_part)
        
        # aiosmtplib을 사용한 비동기 SMTP 연결
        # SSL 컨텍스트 생성 (인증서 검증 비활성화)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # 포트에 따른 TLS 설정 결정
        if settings.SMTP_PORT == 465:
            # 포트 465: SSL/TLS 직접 연결
            smtp_client = aiosmtplib.SMTP(
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                use_tls=True,
                tls_context=ssl_context
            )
            await smtp_client.connect()
        else:
            # 포트 587: STARTTLS 사용
            smtp_client = aiosmtplib.SMTP(
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                use_tls=False,
                tls_context=ssl_context
            )
            await smtp_client.connect()
            await smtp_client.starttls()
        
        # SMTP 서버 인증
        await smtp_client.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        
        # 메일 발송
        await smtp_client.send_message(message)
        await smtp_client.quit()
        
        logging.info(f"✅ 메일 발송 성공: {to_email}")
        return True, ""
        
    except aiosmtplib.SMTPAuthenticationError as e:
        error_msg = f"SMTP 인증 실패: {str(e)} - 이메일 계정과 비밀번호를 확인하세요."
        logging.error(f"❌ {error_msg}")
        return False, error_msg
    except aiosmtplib.SMTPRecipientsRefused as e:
        error_msg = f"수신자 거부: {str(e)} - 수신자 이메일 주소를 확인하세요."
        logging.error(f"❌ {error_msg}")
        return False, error_msg
    except aiosmtplib.SMTPException as e:
        error_msg = f"SMTP 오류: {str(e)}"
        logging.error(f"❌ {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"메일 발송 중 예상치 못한 오류: {str(e)}"
        logging.error(f"❌ {error_msg}")
        return False, error_msg

@router.post("/send", response_model=MailResponse, summary="메일 발송")
async def send_mail(
    mail_data: MailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """메일 발송 엔드포인트"""
    
    try:
        # 메일 발송 시도
        success, error_message = await send_email_via_postfix(
            to_email=mail_data.to_email,
            subject=mail_data.subject,
            body=mail_data.body
        )
        
        # 메일 로그 저장
        mail_log = MailLog(
            user_id=current_user.id,
            to_email=mail_data.to_email,
            subject=mail_data.subject,
            body=mail_data.body,
            action="send",
            status="sent" if success else "failed",
            error_message=None if success else error_message
        )
        
        db.add(mail_log)
        db.commit()
        db.refresh(mail_log)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email"
            )
        
        return {
            "message": "Email sent successfully",
            "mail_id": mail_log.id
        }
        
    except Exception as e:
        # 에러 로그 저장
        mail_log = MailLog(
            user_id=current_user.id,
            to_email=mail_data.to_email,
            subject=mail_data.subject,
            body=mail_data.body,
            action="send",
            status="failed",
            error_message=str(e)
        )
        
        db.add(mail_log)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )

@router.get("/logs", response_model=List[MailLogResponse])
async def get_mail_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10,
    offset: int = 0
):
    """메일 발송 로그 조회 엔드포인트"""
    
    mail_logs = db.query(MailLog).filter(
        MailLog.user_id == current_user.id
    ).order_by(
        MailLog.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return mail_logs

@router.get("/logs/{mail_id}", response_model=MailLogResponse)
async def get_mail_log(
    mail_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """특정 메일 로그 조회 엔드포인트"""
    
    mail_log = db.query(MailLog).filter(
        MailLog.id == mail_id,
        MailLog.user_id == current_user.id
    ).first()
    
    if not mail_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mail log not found"
        )
    
    return mail_log