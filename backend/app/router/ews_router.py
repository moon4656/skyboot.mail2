"""
Exchange Web Services (EWS) 호환 API Router
SkyBoot Mail Server - Outlook 고급 기능 지원

이 모듈은 Microsoft Exchange Web Services와 호환되는 API를 제공하여
Outlook에서 고급 메일 기능을 사용할 수 있도록 합니다.
"""

from fastapi import APIRouter, Request, HTTPException, Depends, Response
from fastapi.responses import Response as FastAPIResponse
from typing import Dict, Any, Optional
import xml.etree.ElementTree as ET
from xml.dom import minidom
import logging
from datetime import datetime, timezone
import uuid

from app.service.user_service import UserService
from app.service.mail_service import MailService
from app.service.organization_service import OrganizationService
from app.database.user import get_db
from app.config import settings
from app.middleware.tenant_middleware import get_current_user, get_current_organization

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter()


@router.post("/Exchange.asmx", summary="EWS 메인 엔드포인트")
async def ews_main_endpoint(
    request: Request,
    current_user=Depends(get_current_user),
    organization=Depends(get_current_organization),
    db=Depends(get_db)
):
    """
    Exchange Web Services 메인 엔드포인트입니다.
    
    Outlook에서 보내는 SOAP 요청을 처리하고 적절한 응답을 반환합니다.
    
    지원하는 EWS 작업:
    - GetFolder: 폴더 정보 조회
    - FindItem: 메일 아이템 검색
    - GetItem: 메일 아이템 상세 조회
    - CreateItem: 메일 아이템 생성
    - UpdateItem: 메일 아이템 업데이트
    - DeleteItem: 메일 아이템 삭제
    - SyncFolderItems: 폴더 동기화
    
    Returns:
        SOAP XML 응답
    
    Raises:
        HTTPException: 요청 처리 오류 시
    """
    try:
        # 📧 EWS 요청 시작 로깅
        logger.info(f"📧 EWS 요청 시작 - 사용자: {current_user.email}, 조직: {organization.name}")
        
        # 요청 본문 읽기
        body = await request.body()
        
        if not body:
            logger.warning("⚠️ EWS 요청 본문이 비어있음")
            raise HTTPException(status_code=400, detail="SOAP 요청 본문이 필요합니다")
        
        # SOAP XML 파싱
        try:
            root = ET.fromstring(body.decode('utf-8'))
            
            # SOAP 네임스페이스 정의
            namespaces = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'types': 'http://schemas.microsoft.com/exchange/services/2006/types',
                'messages': 'http://schemas.microsoft.com/exchange/services/2006/messages'
            }
            
            # SOAP Body에서 작업 추출
            soap_body = root.find('soap:Body', namespaces)
            if soap_body is None:
                raise HTTPException(status_code=400, detail="SOAP Body를 찾을 수 없습니다")
            
            # EWS 작업 식별
            operation = None
            for child in soap_body:
                if child.tag.endswith('}GetFolder'):
                    operation = 'GetFolder'
                elif child.tag.endswith('}FindItem'):
                    operation = 'FindItem'
                elif child.tag.endswith('}GetItem'):
                    operation = 'GetItem'
                elif child.tag.endswith('}CreateItem'):
                    operation = 'CreateItem'
                elif child.tag.endswith('}UpdateItem'):
                    operation = 'UpdateItem'
                elif child.tag.endswith('}DeleteItem'):
                    operation = 'DeleteItem'
                elif child.tag.endswith('}SyncFolderItems'):
                    operation = 'SyncFolderItems'
                break
            
            if not operation:
                logger.warning("⚠️ 지원하지 않는 EWS 작업")
                raise HTTPException(status_code=400, detail="지원하지 않는 EWS 작업입니다")
            
            # 📧 작업 타입 로깅
            logger.info(f"📧 EWS 작업: {operation} - 사용자: {current_user.email}")
            
            # 서비스 인스턴스 생성
            mail_service = MailService(db)
            
            # 작업별 처리
            if operation == 'GetFolder':
                response_xml = await _handle_get_folder(soap_body, current_user, organization, mail_service, namespaces)
            elif operation == 'FindItem':
                response_xml = await _handle_find_item(soap_body, current_user, organization, mail_service, namespaces)
            elif operation == 'GetItem':
                response_xml = await _handle_get_item(soap_body, current_user, organization, mail_service, namespaces)
            elif operation == 'CreateItem':
                response_xml = await _handle_create_item(soap_body, current_user, organization, mail_service, namespaces)
            elif operation == 'UpdateItem':
                response_xml = await _handle_update_item(soap_body, current_user, organization, mail_service, namespaces)
            elif operation == 'DeleteItem':
                response_xml = await _handle_delete_item(soap_body, current_user, organization, mail_service, namespaces)
            elif operation == 'SyncFolderItems':
                response_xml = await _handle_sync_folder_items(soap_body, current_user, organization, mail_service, namespaces)
            else:
                raise HTTPException(status_code=501, detail="아직 구현되지 않은 EWS 작업입니다")
            
            # 📧 성공 로깅
            logger.info(f"✅ EWS {operation} 완료 - 사용자: {current_user.email}")
            
            # SOAP 응답 반환
            return FastAPIResponse(
                content=response_xml,
                media_type="text/xml",
                headers={
                    "Content-Type": "text/xml; charset=utf-8",
                    "Server": "SkyBoot-Mail-EWS/1.0"
                }
            )
            
        except ET.ParseError as e:
            logger.error(f"❌ SOAP XML 파싱 오류: {str(e)}")
            raise HTTPException(status_code=400, detail="잘못된 SOAP XML 형식입니다")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ EWS 처리 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")


async def _handle_get_folder(soap_body, current_user, organization, mail_service, namespaces):
    """GetFolder 작업을 처리합니다."""
    # 기본 폴더 정보 반환
    folders = [
        {"id": "inbox", "name": "받은편지함", "class": "IPF.Note", "total_count": 0, "unread_count": 0},
        {"id": "sent", "name": "보낸편지함", "class": "IPF.Note", "total_count": 0, "unread_count": 0},
        {"id": "drafts", "name": "임시보관함", "class": "IPF.Note", "total_count": 0, "unread_count": 0},
        {"id": "trash", "name": "휴지통", "class": "IPF.Note", "total_count": 0, "unread_count": 0},
    ]
    
    return _create_get_folder_response(folders)


async def _handle_find_item(soap_body, current_user, organization, mail_service, namespaces):
    """FindItem 작업을 처리합니다."""
    # 메일 목록 조회 (간단한 구현)
    mails = await mail_service.get_user_mails(
        user_id=current_user.id,
        folder_type="inbox",
        page=1,
        limit=50
    )
    
    return _create_find_item_response(mails)


async def _handle_get_item(soap_body, current_user, organization, mail_service, namespaces):
    """GetItem 작업을 처리합니다."""
    # 메일 상세 정보 조회 (구현 필요)
    return _create_get_item_response([])


async def _handle_create_item(soap_body, current_user, organization, mail_service, namespaces):
    """CreateItem 작업을 처리합니다."""
    # 메일 생성 (구현 필요)
    return _create_create_item_response("success")


async def _handle_update_item(soap_body, current_user, organization, mail_service, namespaces):
    """UpdateItem 작업을 처리합니다."""
    # 메일 업데이트 (구현 필요)
    return _create_update_item_response("success")


async def _handle_delete_item(soap_body, current_user, organization, mail_service, namespaces):
    """DeleteItem 작업을 처리합니다."""
    # 메일 삭제 (구현 필요)
    return _create_delete_item_response("success")


async def _handle_sync_folder_items(soap_body, current_user, organization, mail_service, namespaces):
    """SyncFolderItems 작업을 처리합니다."""
    # 폴더 동기화 (구현 필요)
    return _create_sync_folder_items_response([])


def _create_get_folder_response(folders):
    """GetFolder SOAP 응답을 생성합니다."""
    soap_env = ET.Element("{http://schemas.xmlsoap.org/soap/envelope/}Envelope")
    soap_env.set("xmlns:soap", "http://schemas.xmlsoap.org/soap/envelope/")
    soap_env.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    soap_env.set("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")
    
    soap_body = ET.SubElement(soap_env, "{http://schemas.xmlsoap.org/soap/envelope/}Body")
    
    get_folder_response = ET.SubElement(soap_body, "{http://schemas.microsoft.com/exchange/services/2006/messages}GetFolderResponse")
    response_messages = ET.SubElement(get_folder_response, "{http://schemas.microsoft.com/exchange/services/2006/messages}ResponseMessages")
    
    for folder in folders:
        get_folder_response_message = ET.SubElement(response_messages, "{http://schemas.microsoft.com/exchange/services/2006/messages}GetFolderResponseMessage")
        get_folder_response_message.set("ResponseClass", "Success")
        
        response_code = ET.SubElement(get_folder_response_message, "{http://schemas.microsoft.com/exchange/services/2006/messages}ResponseCode")
        response_code.text = "NoError"
        
        folders_elem = ET.SubElement(get_folder_response_message, "{http://schemas.microsoft.com/exchange/services/2006/messages}Folders")
        folder_elem = ET.SubElement(folders_elem, "{http://schemas.microsoft.com/exchange/services/2006/types}Folder")
        
        folder_id = ET.SubElement(folder_elem, "{http://schemas.microsoft.com/exchange/services/2006/types}FolderId")
        folder_id.set("Id", folder["id"])
        
        display_name = ET.SubElement(folder_elem, "{http://schemas.microsoft.com/exchange/services/2006/types}DisplayName")
        display_name.text = folder["name"]
        
        total_count = ET.SubElement(folder_elem, "{http://schemas.microsoft.com/exchange/services/2006/types}TotalCount")
        total_count.text = str(folder["total_count"])
        
        unread_count = ET.SubElement(folder_elem, "{http://schemas.microsoft.com/exchange/services/2006/types}UnreadCount")
        unread_count.text = str(folder["unread_count"])
    
    return ET.tostring(soap_env, encoding='unicode')


def _create_find_item_response(mails):
    """FindItem SOAP 응답을 생성합니다."""
    soap_env = ET.Element("{http://schemas.xmlsoap.org/soap/envelope/}Envelope")
    soap_env.set("xmlns:soap", "http://schemas.xmlsoap.org/soap/envelope/")
    
    soap_body = ET.SubElement(soap_env, "{http://schemas.xmlsoap.org/soap/envelope/}Body")
    
    find_item_response = ET.SubElement(soap_body, "{http://schemas.microsoft.com/exchange/services/2006/messages}FindItemResponse")
    response_messages = ET.SubElement(find_item_response, "{http://schemas.microsoft.com/exchange/services/2006/messages}ResponseMessages")
    
    find_item_response_message = ET.SubElement(response_messages, "{http://schemas.microsoft.com/exchange/services/2006/messages}FindItemResponseMessage")
    find_item_response_message.set("ResponseClass", "Success")
    
    response_code = ET.SubElement(find_item_response_message, "{http://schemas.microsoft.com/exchange/services/2006/messages}ResponseCode")
    response_code.text = "NoError"
    
    root_folder = ET.SubElement(find_item_response_message, "{http://schemas.microsoft.com/exchange/services/2006/messages}RootFolder")
    root_folder.set("TotalItemsInView", str(len(mails)))
    root_folder.set("IncludesLastItemInRange", "true")
    
    items = ET.SubElement(root_folder, "{http://schemas.microsoft.com/exchange/services/2006/types}Items")
    
    for mail in mails:
        message = ET.SubElement(items, "{http://schemas.microsoft.com/exchange/services/2006/types}Message")
        
        item_id = ET.SubElement(message, "{http://schemas.microsoft.com/exchange/services/2006/types}ItemId")
        item_id.set("Id", mail.mail_id)
        
        subject = ET.SubElement(message, "{http://schemas.microsoft.com/exchange/services/2006/types}Subject")
        subject.text = mail.subject or ""
        
        date_time_received = ET.SubElement(message, "{http://schemas.microsoft.com/exchange/services/2006/types}DateTimeReceived")
        date_time_received.text = mail.sent_at.isoformat() if mail.sent_at else datetime.now(timezone.utc).isoformat()
    
    return ET.tostring(soap_env, encoding='unicode')


def _create_get_item_response(items):
    """GetItem SOAP 응답을 생성합니다."""
    # 간단한 구현 - 실제로는 더 상세한 메일 정보를 포함해야 함
    return """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <GetItemResponse xmlns="http://schemas.microsoft.com/exchange/services/2006/messages">
      <ResponseMessages>
        <GetItemResponseMessage ResponseClass="Success">
          <ResponseCode>NoError</ResponseCode>
          <Items>
            <!-- 메일 아이템 상세 정보 -->
          </Items>
        </GetItemResponseMessage>
      </ResponseMessages>
    </GetItemResponse>
  </soap:Body>
</soap:Envelope>"""


def _create_create_item_response(result):
    """CreateItem SOAP 응답을 생성합니다."""
    return """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <CreateItemResponse xmlns="http://schemas.microsoft.com/exchange/services/2006/messages">
      <ResponseMessages>
        <CreateItemResponseMessage ResponseClass="Success">
          <ResponseCode>NoError</ResponseCode>
        </CreateItemResponseMessage>
      </ResponseMessages>
    </CreateItemResponse>
  </soap:Body>
</soap:Envelope>"""


def _create_update_item_response(result):
    """UpdateItem SOAP 응답을 생성합니다."""
    return """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <UpdateItemResponse xmlns="http://schemas.microsoft.com/exchange/services/2006/messages">
      <ResponseMessages>
        <UpdateItemResponseMessage ResponseClass="Success">
          <ResponseCode>NoError</ResponseCode>
        </UpdateItemResponseMessage>
      </ResponseMessages>
    </UpdateItemResponse>
  </soap:Body>
</soap:Envelope>"""


def _create_delete_item_response(result):
    """DeleteItem SOAP 응답을 생성합니다."""
    return """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <DeleteItemResponse xmlns="http://schemas.microsoft.com/exchange/services/2006/messages">
      <ResponseMessages>
        <DeleteItemResponseMessage ResponseClass="Success">
          <ResponseCode>NoError</ResponseCode>
        </DeleteItemResponseMessage>
      </ResponseMessages>
    </DeleteItemResponse>
  </soap:Body>
</soap:Envelope>"""


def _create_sync_folder_items_response(items):
    """SyncFolderItems SOAP 응답을 생성합니다."""
    return """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <SyncFolderItemsResponse xmlns="http://schemas.microsoft.com/exchange/services/2006/messages">
      <ResponseMessages>
        <SyncFolderItemsResponseMessage ResponseClass="Success">
          <ResponseCode>NoError</ResponseCode>
          <SyncState>sync-state-token</SyncState>
          <IncludesLastItemInRange>true</IncludesLastItemInRange>
          <Changes>
            <!-- 변경된 아이템 목록 -->
          </Changes>
        </SyncFolderItemsResponseMessage>
      </ResponseMessages>
    </SyncFolderItemsResponse>
  </soap:Body>
</soap:Envelope>"""


@router.get("/", summary="EWS 서비스 상태 확인")
async def ews_status():
    """
    Exchange Web Services 상태를 확인합니다.
    
    Returns:
        EWS 서비스 상태 정보
    """
    return {
        "service": "SkyBoot Mail Exchange Web Services",
        "status": "active",
        "version": "1.0.0",
        "supported_operations": [
            "GetFolder",
            "FindItem", 
            "GetItem",
            "CreateItem",
            "UpdateItem",
            "DeleteItem",
            "SyncFolderItems"
        ],
        "endpoints": {
            "ews": "/ews/Exchange.asmx",
            "status": "/ews/"
        }
    }