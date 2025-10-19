from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
import csv
import io

from app.database.user import get_db
from app.middleware.tenant_middleware import get_current_org_id
from app.service.addressbook_service import AddressBookService
from app.service.auth_service import get_current_user, logger
from app.model.user_model import User

router = APIRouter()

@router.get("/download-csv", summary="연락처 CSV 다운로드")
def download_contacts_csv_file(
    db: Session = Depends(get_db), 
    org_id: str = Depends(get_current_org_id),
    current_user: User = Depends(get_current_user)
):
    """
    조직의 연락처를 CSV 형식으로 다운로드합니다.
    
    Args:
        db: 데이터베이스 세션
        org_id: 조직 ID
        current_user: 현재 사용자
        
    Returns:
        CSV 형식의 연락처 데이터
    """
    logger.info(f"📤 CSV 다운로드 함수 호출됨 - 조직: {org_id}, 사용자: {current_user.email}")
    items, _ = AddressBookService.list_contacts(db, org_id, page=1, size=100000, q=None)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "email", "phone", "mobile", "company", "title", "address"])
    for c in items:
        writer.writerow([c.name or "", c.email or "", c.phone or "", c.mobile or "", c.company or "", c.title or "", (c.address or "").replace('\n',' ')])
    csv_text = output.getvalue()
    
    # CSV 파일로 응답
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contacts.csv"}
    )

@router.get("/export-addressbook-csv", summary="주소록 CSV 내보내기")
def export_addressbook_to_csv(
    db: Session = Depends(get_db), 
    org_id: str = Depends(get_current_org_id),
    current_user: User = Depends(get_current_user)
):
    """
    조직의 주소록을 CSV 형식으로 내보냅니다.
    
    Args:
        db: 데이터베이스 세션
        org_id: 조직 ID
        current_user: 현재 사용자
        
    Returns:
        CSV 형식의 주소록 데이터
    """
    logger.info(f"📋 주소록 CSV 내보내기 시작 - 조직: {org_id}, 사용자: {current_user.email}")
    
    try:
        # 모든 연락처 조회
        contacts, total_count = AddressBookService.list_contacts(db, org_id, page=1, size=100000, q=None)
        logger.info(f"📊 총 {total_count}개의 연락처를 조회했습니다.")
        
        # CSV 데이터 생성
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 헤더 작성
        writer.writerow(["이름", "이메일", "전화번호", "휴대폰", "회사", "직책", "주소"])
        
        # 데이터 작성
        for contact in contacts:
            writer.writerow([
                contact.name or "",
                contact.email or "",
                contact.phone or "",
                contact.mobile or "",
                contact.company or "",
                contact.title or "",
                (contact.address or "").replace('\n', ' ')
            ])
        
        csv_content = output.getvalue()
        logger.info(f"✅ CSV 내보내기 완료 - 조직: {org_id}, 연락처 수: {len(contacts)}")
        
        # CSV 파일로 응답
        return Response(
            content=csv_content,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": "attachment; filename=addressbook_export.csv",
                "Content-Type": "text/csv; charset=utf-8"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ CSV 내보내기 실패 - 조직: {org_id}, 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CSV 내보내기 실패: {str(e)}")