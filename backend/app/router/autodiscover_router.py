"""
Outlook Autodiscover API Router
SkyBoot Mail Server - Outlook 자동 구성 지원

이 모듈은 Microsoft Outlook의 Autodiscover 기능을 지원하여
사용자가 이메일 주소만으로 자동으로 메일 서버 설정을 구성할 수 있도록 합니다.
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import Response
from typing import Dict, Any
import xml.etree.ElementTree as ET
from xml.dom import minidom
import logging

from app.service.user_service import UserService
from app.service.organization_service import OrganizationService
from app.database.user import get_db
from app.config import settings

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(
    prefix="/autodiscover",
    tags=["Autodiscover"],
    responses={404: {"description": "Not found"}}
)


@router.post("/autodiscover.xml", summary="Outlook Autodiscover 설정 제공")
async def autodiscover_xml(
    request: Request,
    db=Depends(get_db)
):
    """
    Microsoft Outlook Autodiscover 요청을 처리합니다.
    
    Outlook에서 POST 요청으로 사용자 이메일 정보를 보내면,
    해당 사용자의 메일 서버 설정 정보를 XML 형태로 반환합니다.
    
    Returns:
        XML 형태의 Autodiscover 응답
    
    Raises:
        HTTPException: 사용자를 찾을 수 없거나 설정 오류 시
    """
    try:
        # 📧 Autodiscover 요청 시작 로깅
        logger.info(f"📧 Autodiscover 요청 시작 - IP: {request.client.host}")
        
        # 요청 본문 읽기
        body = await request.body()
        
        if not body:
            logger.warning("⚠️ Autodiscover 요청 본문이 비어있음")
            raise HTTPException(status_code=400, detail="요청 본문이 필요합니다")
        
        # XML 파싱하여 이메일 주소 추출
        try:
            root = ET.fromstring(body.decode('utf-8'))
            
            # Outlook Autodiscover 네임스페이스 처리
            namespaces = {
                'autodiscover': 'http://schemas.microsoft.com/exchange/autodiscover/outlook/requestschema/2006'
            }
            
            email_element = root.find('.//autodiscover:EMailAddress', namespaces)
            if email_element is None:
                # 네임스페이스 없이 시도
                email_element = root.find('.//EMailAddress')
            
            if email_element is None:
                logger.warning("⚠️ Autodiscover 요청에서 이메일 주소를 찾을 수 없음")
                raise HTTPException(status_code=400, detail="이메일 주소가 필요합니다")
            
            email_address = email_element.text
            
        except ET.ParseError as e:
            logger.error(f"❌ XML 파싱 오류: {str(e)}")
            raise HTTPException(status_code=400, detail="잘못된 XML 형식입니다")
        
        # 📧 이메일 주소 로깅
        logger.info(f"📧 Autodiscover 요청 - 이메일: {email_address}")
        
        # 사용자 및 조직 정보 조회
        user_service = UserService(db)
        org_service = OrganizationService(db)
        
        # 이메일로 사용자 찾기
        user = await user_service.get_user_by_email(email_address)
        if not user:
            logger.warning(f"⚠️ 사용자를 찾을 수 없음 - 이메일: {email_address}")
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 조직 정보 조회
        organization = await org_service.get_organization_by_id(user.organization_id)
        if not organization:
            logger.error(f"❌ 조직을 찾을 수 없음 - 조직ID: {user.organization_id}")
            raise HTTPException(status_code=404, detail="조직 정보를 찾을 수 없습니다")
        
        # Autodiscover 응답 XML 생성
        autodiscover_xml = _create_autodiscover_response(
            email_address=email_address,
            display_name=user.full_name or user.email,
            organization=organization
        )
        
        # 📧 성공 로깅
        logger.info(f"✅ Autodiscover 응답 생성 완료 - 이메일: {email_address}, 조직: {organization.name}")
        
        # XML 응답 반환
        return Response(
            content=autodiscover_xml,
            media_type="application/xml",
            headers={
                "Content-Type": "text/xml; charset=utf-8",
                "Cache-Control": "private, max-age=3600"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Autodiscover 처리 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")


@router.get("/autodiscover.xml", summary="Outlook Autodiscover GET 요청 처리")
async def autodiscover_get(request: Request):
    """
    GET 방식의 Autodiscover 요청을 처리합니다.
    일부 Outlook 버전에서 GET 요청을 먼저 시도하는 경우가 있습니다.
    
    Returns:
        POST 방식 사용을 안내하는 응답
    """
    logger.info(f"📧 Autodiscover GET 요청 - IP: {request.client.host}")
    
    return Response(
        content="POST 방식으로 요청해주세요",
        status_code=405,
        headers={"Allow": "POST"}
    )


def _create_autodiscover_response(
    email_address: str,
    display_name: str,
    organization: Any
) -> str:
    """
    Outlook Autodiscover XML 응답을 생성합니다.
    
    Args:
        email_address: 사용자 이메일 주소
        display_name: 사용자 표시 이름
        organization: 조직 정보
    
    Returns:
        XML 형태의 Autodiscover 응답 문자열
    """
    # 서버 도메인 설정 (조직 도메인 또는 기본 도메인)
    server_domain = organization.domain or settings.DEFAULT_MAIL_DOMAIN
    
    # XML 루트 엘리먼트 생성
    autodiscover = ET.Element("Autodiscover")
    autodiscover.set("xmlns", "http://schemas.microsoft.com/exchange/autodiscover/responseschema/2006")
    
    # Response 엘리먼트
    response = ET.SubElement(autodiscover, "Response")
    response.set("xmlns", "http://schemas.microsoft.com/exchange/autodiscover/outlook/responseschema/2006a")
    
    # User 정보
    user_elem = ET.SubElement(response, "User")
    ET.SubElement(user_elem, "DisplayName").text = display_name
    ET.SubElement(user_elem, "LegacyDN").text = f"/o={organization.name}/ou=Exchange Administrative Group (FYDIBOHF23SPDLT)/cn=Recipients/cn={email_address}"
    ET.SubElement(user_elem, "AutoDiscoverSMTPAddress").text = email_address
    ET.SubElement(user_elem, "DeploymentId").text = organization.org_uuid
    
    # Account 정보
    account = ET.SubElement(response, "Account")
    ET.SubElement(account, "AccountType").text = "email"
    ET.SubElement(account, "Action").text = "settings"
    ET.SubElement(account, "MicrosoftOnline").text = "False"
    
    # IMAP 프로토콜 설정
    imap_protocol = ET.SubElement(account, "Protocol")
    ET.SubElement(imap_protocol, "Type").text = "IMAP"
    ET.SubElement(imap_protocol, "Server").text = server_domain
    ET.SubElement(imap_protocol, "Port").text = "993"  # IMAPS 포트
    ET.SubElement(imap_protocol, "DomainRequired").text = "false"
    ET.SubElement(imap_protocol, "LoginName").text = email_address
    ET.SubElement(imap_protocol, "SPA").text = "false"
    ET.SubElement(imap_protocol, "SSL").text = "on"
    ET.SubElement(imap_protocol, "AuthRequired").text = "on"
    
    # SMTP 프로토콜 설정
    smtp_protocol = ET.SubElement(account, "Protocol")
    ET.SubElement(smtp_protocol, "Type").text = "SMTP"
    ET.SubElement(smtp_protocol, "Server").text = server_domain
    ET.SubElement(smtp_protocol, "Port").text = "587"  # SMTP 제출 포트
    ET.SubElement(smtp_protocol, "DomainRequired").text = "false"
    ET.SubElement(smtp_protocol, "LoginName").text = email_address
    ET.SubElement(smtp_protocol, "SPA").text = "false"
    ET.SubElement(smtp_protocol, "Encryption").text = "TLS"
    ET.SubElement(smtp_protocol, "AuthRequired").text = "on"
    ET.SubElement(smtp_protocol, "UsePOPAuth").text = "on"
    ET.SubElement(smtp_protocol, "SMTPLast").text = "off"
    
    # XML을 문자열로 변환하고 포맷팅
    rough_string = ET.tostring(autodiscover, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    
    # UTF-8 선언과 함께 반환
    xml_declaration = '<?xml version="1.0" encoding="utf-8"?>'
    formatted_xml = reparsed.documentElement.toprettyxml(indent="  ")
    
    return xml_declaration + "\n" + formatted_xml


@router.get("/", summary="Autodiscover 서비스 상태 확인")
async def autodiscover_status():
    """
    Autodiscover 서비스 상태를 확인합니다.
    
    Returns:
        서비스 상태 정보
    """
    return {
        "service": "SkyBoot Mail Autodiscover",
        "status": "active",
        "version": "1.0.0",
        "supported_clients": ["Microsoft Outlook", "Outlook Express", "Windows Mail"],
        "endpoints": {
            "autodiscover": "/autodiscover/autodiscover.xml",
            "status": "/autodiscover/"
        }
    }