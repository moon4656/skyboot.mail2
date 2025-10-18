"""
Microsoft Graph API 연동 Router
SkyBoot Mail Server - Office 365 통합 지원

이 모듈은 Microsoft Graph API와 연동하여 Office 365 환경과
SkyBoot Mail 서버 간의 메일 동기화 및 통합 기능을 제공합니다.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from typing import Dict, Any, Optional, List
import httpx
import json
import logging
from datetime import datetime, timedelta
import base64
from urllib.parse import urlencode

from app.service.user_service import UserService
from app.service.mail_service import MailService
from app.service.organization_service import OrganizationService
from app.database.user import get_db
from app.config import settings
from app.middleware.tenant_middleware import get_current_user, get_current_organization
from app.schemas.mail_schema import MailSendRequest

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(
    prefix="/graph",
    tags=["Microsoft Graph API"],
    responses={404: {"description": "Not found"}}
)

# Microsoft Graph API 설정
GRAPH_API_BASE_URL = "https://graph.microsoft.com/v1.0"
GRAPH_AUTH_URL = "https://login.microsoftonline.com"


@router.get("/auth/login", summary="Microsoft 계정 로그인")
async def microsoft_login(
    request: Request,
    current_user=Depends(get_current_user),
    organization=Depends(get_current_organization)
):
    """
    Microsoft 계정으로 로그인하여 Graph API 액세스 토큰을 획득합니다.
    
    OAuth 2.0 인증 플로우를 시작하여 사용자를 Microsoft 로그인 페이지로 리디렉션합니다.
    
    Returns:
        Microsoft 로그인 페이지로의 리디렉션
    """
    try:
        # 📧 Microsoft 로그인 시작 로깅
        logger.info(f"📧 Microsoft 로그인 시작 - 사용자: {current_user.email}, 조직: {organization.name}")
        
        # OAuth 2.0 파라미터 설정
        auth_params = {
            "client_id": settings.MICROSOFT_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": f"{settings.BASE_URL}/api/v1/graph/auth/callback",
            "scope": "https://graph.microsoft.com/Mail.ReadWrite https://graph.microsoft.com/Mail.Send offline_access",
            "state": f"{current_user.id}:{organization.id}",  # 사용자 및 조직 정보 포함
            "response_mode": "query"
        }
        
        # Microsoft 로그인 URL 생성
        auth_url = f"{GRAPH_AUTH_URL}/common/oauth2/v2.0/authorize?{urlencode(auth_params)}"
        
        # 📧 리디렉션 로깅
        logger.info(f"📧 Microsoft 로그인 리디렉션 - URL: {auth_url}")
        
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        logger.error(f"❌ Microsoft 로그인 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="Microsoft 로그인 처리 중 오류가 발생했습니다")


@router.get("/auth/callback", summary="Microsoft 인증 콜백")
async def microsoft_auth_callback(
    code: str,
    state: str,
    db=Depends(get_db)
):
    """
    Microsoft OAuth 인증 콜백을 처리합니다.
    
    인증 코드를 액세스 토큰으로 교환하고 사용자 정보를 저장합니다.
    
    Args:
        code: Microsoft에서 반환된 인증 코드
        state: 사용자 및 조직 정보가 포함된 상태 값
    
    Returns:
        인증 성공 메시지 및 토큰 정보
    """
    try:
        # 📧 콜백 처리 시작 로깅
        logger.info(f"📧 Microsoft 인증 콜백 처리 시작 - state: {state}")
        
        # State에서 사용자 및 조직 ID 추출
        try:
            user_id, org_id = state.split(":")
            user_id = int(user_id)
            org_id = int(org_id)
        except ValueError:
            logger.error("❌ 잘못된 state 파라미터")
            raise HTTPException(status_code=400, detail="잘못된 인증 상태입니다")
        
        # 액세스 토큰 요청
        token_data = {
            "client_id": settings.MICROSOFT_CLIENT_ID,
            "client_secret": settings.MICROSOFT_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": f"{settings.BASE_URL}/api/v1/graph/auth/callback"
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                f"{GRAPH_AUTH_URL}/common/oauth2/v2.0/token",
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
        
        if token_response.status_code != 200:
            logger.error(f"❌ 토큰 요청 실패: {token_response.text}")
            raise HTTPException(status_code=400, detail="액세스 토큰 획득에 실패했습니다")
        
        token_info = token_response.json()
        access_token = token_info.get("access_token")
        refresh_token = token_info.get("refresh_token")
        expires_in = token_info.get("expires_in", 3600)
        
        # 사용자 정보 업데이트 (토큰 저장)
        user_service = UserService(db)
        await user_service.update_microsoft_tokens(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(seconds=expires_in)
        )
        
        # 📧 성공 로깅
        logger.info(f"✅ Microsoft 인증 완료 - 사용자ID: {user_id}")
        
        return {
            "message": "Microsoft 계정 연동이 완료되었습니다",
            "status": "success",
            "expires_in": expires_in
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Microsoft 인증 콜백 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="인증 처리 중 오류가 발생했습니다")


@router.post("/mail/send", summary="Graph API를 통한 메일 발송")
async def send_mail_via_graph(
    mail_data: MailSendRequest,
    current_user=Depends(get_current_user),
    organization=Depends(get_current_organization),
    db=Depends(get_db)
):
    """
    Microsoft Graph API를 통해 메일을 발송합니다.
    
    사용자의 Microsoft 계정을 통해 메일을 발송하므로
    Office 365 환경과 완전히 통합됩니다.
    
    Args:
        mail_data: 메일 발송 요청 데이터
    
    Returns:
        메일 발송 결과
    """
    try:
        # 📧 Graph API 메일 발송 시작 로깅
        logger.info(f"📧 Graph API 메일 발송 시작 - 사용자: {current_user.email}, 수신자: {mail_data.recipient}")
        
        # 사용자의 Microsoft 액세스 토큰 확인
        user_service = UserService(db)
        access_token = await user_service.get_microsoft_access_token(current_user.id)
        
        if not access_token:
            logger.warning(f"⚠️ Microsoft 토큰 없음 - 사용자: {current_user.email}")
            raise HTTPException(status_code=401, detail="Microsoft 계정 연동이 필요합니다")
        
        # Graph API 메일 발송 요청 구성
        mail_message = {
            "message": {
                "subject": mail_data.subject,
                "body": {
                    "contentType": "HTML" if mail_data.is_html else "Text",
                    "content": mail_data.content
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": recipient.strip()
                        }
                    } for recipient in mail_data.recipient.split(",")
                ],
                "from": {
                    "emailAddress": {
                        "address": current_user.email,
                        "name": current_user.full_name or current_user.email
                    }
                }
            },
            "saveToSentItems": True
        }
        
        # CC 수신자 추가
        if mail_data.cc:
            mail_message["message"]["ccRecipients"] = [
                {
                    "emailAddress": {
                        "address": cc.strip()
                    }
                } for cc in mail_data.cc.split(",")
            ]
        
        # BCC 수신자 추가
        if mail_data.bcc:
            mail_message["message"]["bccRecipients"] = [
                {
                    "emailAddress": {
                        "address": bcc.strip()
                    }
                } for bcc in mail_data.bcc.split(",")
            ]
        
        # 첨부파일 처리 (구현 필요)
        if mail_data.attachments:
            attachments = []
            for attachment in mail_data.attachments:
                # 첨부파일을 base64로 인코딩하여 추가
                attachment_data = {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": attachment.filename,
                    "contentBytes": base64.b64encode(attachment.file.read()).decode()
                }
                attachments.append(attachment_data)
            
            mail_message["message"]["attachments"] = attachments
        
        # Graph API 호출
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GRAPH_API_BASE_URL}/me/sendMail",
                json=mail_message,
                headers=headers
            )
        
        if response.status_code == 202:  # Accepted
            # 📧 성공 로깅
            logger.info(f"✅ Graph API 메일 발송 완료 - 사용자: {current_user.email}, 수신자: {mail_data.recipient}")
            
            return {
                "message": "메일이 성공적으로 발송되었습니다",
                "status": "sent",
                "provider": "Microsoft Graph API",
                "sent_at": datetime.utcnow().isoformat()
            }
        else:
            logger.error(f"❌ Graph API 메일 발송 실패: {response.status_code} - {response.text}")
            raise HTTPException(status_code=400, detail="메일 발송에 실패했습니다")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Graph API 메일 발송 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="메일 발송 중 오류가 발생했습니다")


@router.get("/mail/inbox", summary="Graph API를 통한 받은편지함 조회")
async def get_inbox_via_graph(
    current_user=Depends(get_current_user),
    organization=Depends(get_current_organization),
    db=Depends(get_db),
    top: int = 20,
    skip: int = 0
):
    """
    Microsoft Graph API를 통해 사용자의 받은편지함을 조회합니다.
    
    Args:
        top: 조회할 메일 수 (기본값: 20)
        skip: 건너뛸 메일 수 (기본값: 0)
    
    Returns:
        받은편지함 메일 목록
    """
    try:
        # 📧 Graph API 받은편지함 조회 시작 로깅
        logger.info(f"📧 Graph API 받은편지함 조회 시작 - 사용자: {current_user.email}")
        
        # 사용자의 Microsoft 액세스 토큰 확인
        user_service = UserService(db)
        access_token = await user_service.get_microsoft_access_token(current_user.id)
        
        if not access_token:
            logger.warning(f"⚠️ Microsoft 토큰 없음 - 사용자: {current_user.email}")
            raise HTTPException(status_code=401, detail="Microsoft 계정 연동이 필요합니다")
        
        # Graph API 호출
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        params = {
            "$top": top,
            "$skip": skip,
            "$orderby": "receivedDateTime desc",
            "$select": "id,subject,from,receivedDateTime,isRead,bodyPreview"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GRAPH_API_BASE_URL}/me/mailFolders/inbox/messages",
                headers=headers,
                params=params
            )
        
        if response.status_code == 200:
            data = response.json()
            mails = data.get("value", [])
            
            # 📧 성공 로깅
            logger.info(f"✅ Graph API 받은편지함 조회 완료 - 사용자: {current_user.email}, 메일 수: {len(mails)}")
            
            return {
                "mails": mails,
                "total_count": len(mails),
                "has_more": "@odata.nextLink" in data
            }
        else:
            logger.error(f"❌ Graph API 받은편지함 조회 실패: {response.status_code} - {response.text}")
            raise HTTPException(status_code=400, detail="받은편지함 조회에 실패했습니다")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Graph API 받은편지함 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="받은편지함 조회 중 오류가 발생했습니다")


@router.post("/sync/import", summary="Office 365 메일 가져오기")
async def import_office365_mails(
    current_user=Depends(get_current_user),
    organization=Depends(get_current_organization),
    db=Depends(get_db),
    folder_name: str = "inbox",
    limit: int = 100
):
    """
    Office 365에서 SkyBoot Mail 서버로 메일을 가져옵니다.
    
    Args:
        folder_name: 가져올 폴더명 (기본값: inbox)
        limit: 가져올 메일 수 제한 (기본값: 100)
    
    Returns:
        메일 가져오기 결과
    """
    try:
        # 📧 Office 365 메일 가져오기 시작 로깅
        logger.info(f"📧 Office 365 메일 가져오기 시작 - 사용자: {current_user.email}, 폴더: {folder_name}")
        
        # 사용자의 Microsoft 액세스 토큰 확인
        user_service = UserService(db)
        access_token = await user_service.get_microsoft_access_token(current_user.id)
        
        if not access_token:
            raise HTTPException(status_code=401, detail="Microsoft 계정 연동이 필요합니다")
        
        # Graph API를 통해 메일 조회
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        params = {
            "$top": limit,
            "$orderby": "receivedDateTime desc"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GRAPH_API_BASE_URL}/me/mailFolders/{folder_name}/messages",
                headers=headers,
                params=params
            )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Office 365 메일 조회에 실패했습니다")
        
        mails_data = response.json().get("value", [])
        
        # SkyBoot Mail 서버에 메일 저장
        mail_service = MailService(db)
        imported_count = 0
        
        for mail_data in mails_data:
            try:
                # 메일 데이터 변환 및 저장
                await mail_service.import_mail_from_graph(
                    user_id=current_user.id,
                    organization_id=organization.id,
                    graph_mail_data=mail_data
                )
                imported_count += 1
                
            except Exception as e:
                logger.warning(f"⚠️ 메일 가져오기 실패 - ID: {mail_data.get('id')}, 오류: {str(e)}")
                continue
        
        # 📧 성공 로깅
        logger.info(f"✅ Office 365 메일 가져오기 완료 - 사용자: {current_user.email}, 가져온 메일: {imported_count}/{len(mails_data)}")
        
        return {
            "message": "Office 365 메일 가져오기가 완료되었습니다",
            "imported_count": imported_count,
            "total_count": len(mails_data),
            "folder": folder_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Office 365 메일 가져오기 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="메일 가져오기 중 오류가 발생했습니다")


@router.delete("/auth/disconnect", summary="Microsoft 계정 연동 해제")
async def disconnect_microsoft_account(
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Microsoft 계정 연동을 해제합니다.
    
    저장된 액세스 토큰과 리프레시 토큰을 삭제합니다.
    
    Returns:
        연동 해제 결과
    """
    try:
        # 📧 Microsoft 계정 연동 해제 시작 로깅
        logger.info(f"📧 Microsoft 계정 연동 해제 시작 - 사용자: {current_user.email}")
        
        # 사용자의 Microsoft 토큰 삭제
        user_service = UserService(db)
        await user_service.clear_microsoft_tokens(current_user.id)
        
        # 📧 성공 로깅
        logger.info(f"✅ Microsoft 계정 연동 해제 완료 - 사용자: {current_user.email}")
        
        return {
            "message": "Microsoft 계정 연동이 해제되었습니다",
            "status": "disconnected"
        }
        
    except Exception as e:
        logger.error(f"❌ Microsoft 계정 연동 해제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="연동 해제 중 오류가 발생했습니다")


@router.get("/", summary="Graph API 서비스 상태 확인")
async def graph_api_status():
    """
    Microsoft Graph API 연동 서비스 상태를 확인합니다.
    
    Returns:
        서비스 상태 정보
    """
    return {
        "service": "SkyBoot Mail Microsoft Graph API Integration",
        "status": "active",
        "version": "1.0.0",
        "supported_features": [
            "OAuth 2.0 인증",
            "메일 발송",
            "받은편지함 조회",
            "메일 가져오기",
            "계정 연동 관리"
        ],
        "endpoints": {
            "auth_login": "/graph/auth/login",
            "auth_callback": "/graph/auth/callback",
            "send_mail": "/graph/mail/send",
            "get_inbox": "/graph/mail/inbox",
            "import_mails": "/graph/sync/import",
            "disconnect": "/graph/auth/disconnect",
            "status": "/graph/"
        }
    }