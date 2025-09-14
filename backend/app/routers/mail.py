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
import aiosmtplib
import ssl

router = APIRouter()

async def send_email_via_postfix(to_email: str, subject: str, body: str) -> tuple[bool, str]:
    """
    Postfix를 통한 비동기 이메일 발송 함수
    
    Args:
        to_email: 수신자 이메일
        subject: 메일 제목
        body: 메일 본문
    
    Returns:
        tuple[bool, str]: (발송 성공 여부, 에러 메시지)
    """
    try:
        # MIME 메시지 생성
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = Header(subject, 'utf-8')
        msg['Date'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
        msg['Message-ID'] = f"<{datetime.utcnow().timestamp()}@{socket.getfqdn()}>"
        
        # 텍스트 본문 추가
        text_part = MIMEText(body, 'plain', 'utf-8')
        msg.attach(text_part)
        
        # HTML 본문 추가 (선택사항)
        html_body = f"""
        <html>
          <body>
            <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
              <h2 style="color: #2c3e50;">SkyBoot Mail</h2>
              <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                {body.replace(chr(10), '<br>')}
              </div>
              <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
              <p style="font-size: 12px; color: #666;">
                이 메일은 SkyBoot Mail 시스템에서 발송되었습니다.
              </p>
            </div>
          </body>
        </html>
        """
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(html_part)
        
        # SSL 컨텍스트 생성 (인증서 검증 비활성화)
        tls_context = ssl.create_default_context()
        tls_context.check_hostname = False
        tls_context.verify_mode = ssl.CERT_NONE

        # 비동기 SMTP 연결 및 발송
        smtp_client = aiosmtplib.SMTP(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            timeout=30,
            tls_context=tls_context
        )
        
        await smtp_client.connect()
        
        # 인증이 필요한 경우
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            await smtp_client.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        
        # 메일 발송
        await smtp_client.send_message(msg)
        await smtp_client.quit()
        
        logging.info(f"메일 발송 성공: {to_email}")
        return True, ""
        
    except aiosmtplib.SMTPException as e:
        error_msg = f"SMTP 에러: {str(e)}"
        logging.error(f"메일 발송 실패 - {error_msg}")
        return False, error_msg
    except socket.gaierror as e:
        error_msg = f"네트워크 연결 에러: {str(e)}"
        logging.error(f"메일 발송 실패 - {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"알 수 없는 에러: {str(e)}"
        logging.error(f"메일 발송 실패 - {error_msg}")
        return False, error_msg

@router.post("/send", response_model=MailResponse)
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