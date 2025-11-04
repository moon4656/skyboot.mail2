from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import csv
import io

from ..database.user import get_db
from ..middleware.tenant_middleware import get_current_org_id
from ..service.addressbook_service import AddressBookService
from ..model.addressbook_model import Contact
from ..service.auth_service import get_current_user, logger
from ..model.user_model import User
from ..schemas.addressbook_schema import (
    ContactCreate, ContactUpdate, ContactOut, PaginatedContacts,
    GroupCreate, GroupUpdate, GroupOut,
    DepartmentCreate, DepartmentUpdate, DepartmentOut
)

router = APIRouter()


@router.get("/contacts", response_model=PaginatedContacts, summary="연락처 목록 조회")
def list_contacts(
    page: int = 1,
    size: int = 20,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
    current_user: User = Depends(get_current_user)
):
    items, total = AddressBookService.list_contacts(db, org_id, page, size, q)
    # 그룹 정보 포함 변환
    def to_out(c):
        groups = [GroupOut.from_orm(link.group) for link in c.group_links]
        return ContactOut(
            contact_uuid=c.contact_uuid,
            name=c.name,
            email=c.email,
            phone=c.phone,
            mobile=c.mobile,
            company=c.company,
            title=c.title,
            department_id=c.department_id,
            address=c.address,
            memo=c.memo,
            favorite=c.favorite,
            profile_image_url=c.profile_image_url,
            groups=groups
        )
    return {"items": [to_out(c) for c in items], "total": total, "page": page, "size": size}


@router.post("/contacts", response_model=ContactOut, summary="연락처 생성")
def create_contact(
    body: ContactCreate,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
    current_user: User = Depends(get_current_user)
):
    try:
        contact = AddressBookService.create_contact(db, org_id, body.dict(exclude_unset=True))
        return ContactOut(
            contact_uuid=contact.contact_uuid,
            name=contact.name,
            email=contact.email,
            phone=contact.phone,
            mobile=contact.mobile,
            company=contact.company,
            title=contact.title,
            department_id=contact.department_id,
            address=contact.address,
            memo=contact.memo,
            favorite=contact.favorite,
            profile_image_url=contact.profile_image_url,
            groups=[]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"연락처 생성 실패: {str(e)}")





# 새로운 CSV 내보내기 엔드포인트 - 완전히 다른 이름과 경로 (임시 주석 처리)
# @router.get("/export-addressbook-csv", summary="주소록 CSV 내보내기")
# def export_addressbook_to_csv(
#     db: Session = Depends(get_db), 
#     org_id: str = Depends(get_current_org_id),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     조직의 주소록을 CSV 형식으로 내보냅니다.
#     
#     Args:
#         db: 데이터베이스 세션
#         org_id: 조직 ID
#         current_user: 현재 사용자
#         
#     Returns:
#         CSV 형식의 주소록 데이터
#     """
#     logger.info(f"📋 주소록 CSV 내보내기 시작 - 조직: {org_id}, 사용자: {current_user.email}")
#     
#     try:
#         # 모든 연락처 조회
#         contacts, total_count = AddressBookService.list_contacts(db, org_id, page=1, size=100000, q=None)
#         logger.info(f"📊 총 {total_count}개의 연락처를 조회했습니다.")
#         
#         # CSV 데이터 생성
#         output = io.StringIO()
#         writer = csv.writer(output)
#         
#         # 헤더 작성
#         writer.writerow(["이름", "이메일", "전화번호", "휴대폰", "회사", "직책", "주소"])
#         
#         # 데이터 작성
#         for contact in contacts:
#             writer.writerow([
#                 contact.name or "",
#                 contact.email or "",
#                 contact.phone or "",
#                 contact.mobile or "",
#                 contact.company or "",
#                 contact.title or "",
#                 (contact.address or "").replace('\n', ' ')
#             ])
#         
#         csv_content = output.getvalue()
#         logger.info(f"✅ CSV 내보내기 완료 - 조직: {org_id}, 연락처 수: {len(contacts)}")
#         
#         # CSV 파일로 응답
#         return Response(
#             content=csv_content,
#             media_type="text/csv; charset=utf-8",
#             headers={
#                 "Content-Disposition": "attachment; filename=addressbook_export.csv",
#                 "Content-Type": "text/csv; charset=utf-8"
#             }
#         )
#         
#     except Exception as e:
#         logger.error(f"❌ CSV 내보내기 실패 - 조직: {org_id}, 오류: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"CSV 내보내기 실패: {str(e)}")


@router.get("/contacts/{contact_uuid}", response_model=ContactOut, summary="연락처 상세 조회")
def get_contact(contact_uuid: str, db: Session = Depends(get_db), org_id: str = Depends(get_current_org_id), current_user: User = Depends(get_current_user)):
    contact = AddressBookService.get_contact(db, org_id, contact_uuid)
    if not contact:
        raise HTTPException(status_code=404, detail="연락처를 찾을 수 없습니다")
    groups = [GroupOut.from_orm(link.group) for link in contact.group_links]
    return ContactOut(
        contact_uuid=contact.contact_uuid,
        name=contact.name,
        email=contact.email,
        phone=contact.phone,
        mobile=contact.mobile,
        company=contact.company,
        title=contact.title,
        department_id=contact.department_id,
        address=contact.address,
        memo=contact.memo,
        favorite=contact.favorite,
        profile_image_url=contact.profile_image_url,
        groups=groups
    )


@router.put("/contacts/{contact_uuid}", response_model=ContactOut, summary="연락처 수정")
def update_contact(contact_uuid: str, body: ContactUpdate, db: Session = Depends(get_db), org_id: str = Depends(get_current_org_id), current_user: User = Depends(get_current_user)):
    try:
        contact = AddressBookService.update_contact(db, org_id, contact_uuid, body.dict(exclude_unset=True))
        if not contact:
            raise HTTPException(status_code=404, detail="연락처를 찾을 수 없습니다")
        groups = [GroupOut.from_orm(link.group) for link in contact.group_links]
        return ContactOut(
            contact_uuid=contact.contact_uuid,
            name=contact.name,
            email=contact.email,
            phone=contact.phone,
            mobile=contact.mobile,
            company=contact.company,
            title=contact.title,
            department_id=contact.department_id,
            address=contact.address,
            memo=contact.memo,
            favorite=contact.favorite,
            profile_image_url=contact.profile_image_url,
            groups=groups
        )
    except Exception as e:
        msg = str(e)
        if "이미 존재하는 이메일" in msg:
            raise HTTPException(status_code=409, detail=msg)
        elif "유효하지 않은 부서 ID" in msg:
            raise HTTPException(status_code=400, detail=msg)
        else:
            raise HTTPException(status_code=400, detail=f"연락처 수정 실패: {msg}")


@router.delete("/contacts/{contact_uuid}", summary="연락처 삭제")
def delete_contact(contact_uuid: str, db: Session = Depends(get_db), org_id: str = Depends(get_current_org_id), current_user: User = Depends(get_current_user)):
    ok = AddressBookService.delete_contact(db, org_id, contact_uuid)
    if not ok:
        raise HTTPException(status_code=404, detail="연락처를 찾을 수 없습니다")
    return {"success": True}


# Groups
@router.get("/groups", response_model=list[GroupOut], summary="그룹 목록 조회")
def list_groups(db: Session = Depends(get_db), org_id: str = Depends(get_current_org_id), current_user: User = Depends(get_current_user)):
    groups = AddressBookService.list_groups(db, org_id)
    return [GroupOut.from_orm(g) for g in groups]


@router.post("/groups", response_model=GroupOut, summary="그룹 생성")
def create_group(
    body: GroupCreate, 
    db: Session = Depends(get_db), 
    org_id: str = Depends(get_current_org_id),
    current_user: User = Depends(get_current_user)
):
    """
    새로운 그룹을 생성합니다.
    
    Args:
        body: 그룹 생성 데이터
        db: 데이터베이스 세션
        org_id: 조직 ID
        current_user: 현재 사용자
        
    Returns:
        생성된 그룹 정보
        
    Raises:
        HTTPException: 중복된 그룹명이 있는 경우 409 Conflict
    """
    try:
        group = AddressBookService.create_group(db, org_id, body.name, body.description)
        return GroupOut.from_orm(group)
    except IntegrityError as e:
        db.rollback()
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(
                status_code=409, 
                detail=f"이미 존재하는 그룹명입니다: {body.name}"
            )
        raise HTTPException(
            status_code=400,
            detail=f"그룹 생성 실패: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"그룹 생성 실패: {str(e)}"
        )


@router.put("/groups/{group_id}", response_model=GroupOut, summary="그룹 수정")
def update_group(group_id: int, body: GroupUpdate, db: Session = Depends(get_db), org_id: str = Depends(get_current_org_id), current_user: User = Depends(get_current_user)):
    group = AddressBookService.update_group(db, org_id, group_id, body.dict(exclude_unset=True))
    if not group:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다")
    return GroupOut.from_orm(group)


@router.delete("/groups/{group_id}", summary="그룹 삭제")
def delete_group(group_id: int, db: Session = Depends(get_db), org_id: str = Depends(get_current_org_id), current_user: User = Depends(get_current_user)):
    ok = AddressBookService.delete_group(db, org_id, group_id)
    if not ok:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다")
    return {"success": True}


@router.post("/contacts/{contact_uuid}/groups/{group_id}", summary="연락처를 그룹에 추가")
def add_to_group(contact_uuid: str, group_id: int, db: Session = Depends(get_db), org_id: str = Depends(get_current_org_id), current_user: User = Depends(get_current_user)):
    try:
        ok = AddressBookService.add_contact_to_group(db, org_id, contact_uuid, group_id)
        if not ok:
            raise HTTPException(status_code=404, detail="연락처/그룹을 찾을 수 없습니다")
        return {"success": True}
    except Exception as e:
        msg = str(e)
        # 조직 불일치는 권한 문제로 간주 (403)
        if "현재 조직에 속하지 않은" in msg:
            raise HTTPException(status_code=403, detail=msg)
        # 리소스 미존재는 404로 매핑
        elif "연락처를 찾을 수 없습니다" in msg or "그룹을 찾을 수 없습니다" in msg:
            raise HTTPException(status_code=404, detail=msg)
        # 기타 오류는 400으로 매핑
        raise HTTPException(status_code=400, detail=f"그룹 추가 실패: {msg}")


@router.delete("/contacts/{contact_uuid}/groups/{group_id}", summary="연락처를 그룹에서 제거")
def remove_from_group(contact_uuid: str, group_id: int, db: Session = Depends(get_db), org_id: str = Depends(get_current_org_id), current_user: User = Depends(get_current_user)):
    ok = AddressBookService.remove_contact_from_group(db, org_id, contact_uuid, group_id)
    if not ok:
        raise HTTPException(status_code=404, detail="연락처/그룹 링크를 찾을 수 없습니다")
    return {"success": True}


# Departments
@router.get("/departments", response_model=list[DepartmentOut], summary="부서 목록 조회")
def list_departments(
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
    current_user: User = Depends(get_current_user)
):
    """조직 내 모든 부서를 조회합니다."""
    departments = AddressBookService.list_departments(db, org_id)
    return [DepartmentOut.from_orm(d) for d in departments]


@router.get("/departments/{department_id}", response_model=DepartmentOut, summary="부서 상세 조회")
def get_department(
    department_id: int,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
    current_user: User = Depends(get_current_user)
):
    """특정 부서의 상세 정보를 조회합니다."""
    dept = AddressBookService.get_department(db, org_id, department_id)
    if not dept:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")
    return DepartmentOut.from_orm(dept)


@router.post("/departments", response_model=DepartmentOut, summary="부서 생성")
def create_department(
    body: DepartmentCreate,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
    current_user: User = Depends(get_current_user)
):
    """새로운 부서를 생성합니다."""
    try:
        dept = AddressBookService.create_department(db, org_id, body.name, body.parent_id)
        return DepartmentOut.from_orm(dept)
    except Exception as e:
        # 중복 이름 또는 유효하지 않은 상위 부서 등의 오류
        msg = str(e)
        if "존재하는 부서명" in msg:
            raise HTTPException(status_code=409, detail=msg)
        raise HTTPException(status_code=400, detail=f"부서 생성 실패: {msg}")


@router.put("/departments/{department_id}", response_model=DepartmentOut, summary="부서 수정")
def update_department(
    department_id: int,
    body: DepartmentUpdate,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
    current_user: User = Depends(get_current_user)
):
    """부서 정보를 수정합니다."""
    try:
        dept = AddressBookService.update_department(db, org_id, department_id, body.dict(exclude_unset=True))
        if not dept:
            raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")
        return DepartmentOut.from_orm(dept)
    except Exception as e:
        msg = str(e)
        if "존재하는 부서명" in msg:
            raise HTTPException(status_code=409, detail=msg)
        raise HTTPException(status_code=400, detail=f"부서 수정 실패: {msg}")


@router.delete("/departments/{department_id}", summary="부서 삭제")
def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
    current_user: User = Depends(get_current_user)
):
    """
    부서를 삭제합니다. 하위 부서나 참조 중인 연락처가 있는 경우 409를 반환합니다.
    """
    try:
        ok = AddressBookService.delete_department(db, org_id, department_id)
        if not ok:
            raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다")
        return {"success": True}
    except Exception as e:
        msg = str(e)
        if "삭제할 수 없습니다" in msg:
            raise HTTPException(status_code=409, detail=msg)
        raise HTTPException(status_code=400, detail=f"부서 삭제 실패: {msg}")


@router.post("/contacts/import", summary="연락처 CSV 가져오기")
async def import_contacts(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
    current_user: User = Depends(get_current_user)
):
    """
    CSV 파일에서 연락처를 일괄 생성합니다.

    - 오류가 발생한 행은 건너뛰고, 오류 내역을 함께 반환합니다.
    - 허용 필드: name, email, phone, mobile, company, title, department_id, address, memo, favorite, profile_image_url
    """
    content = await file.read()
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    imported = 0
    errors: list[dict] = []

    for idx, row in enumerate(reader, start=2):  # 1행은 헤더이므로 데이터는 2행부터
        try:
            # 입력 정규화
            name = (row.get("name") or "").strip()
            email = (row.get("email") or None)
            email = email.strip().lower() if isinstance(email, str) and email.strip() else None

            # 선택 필드 파싱
            department_raw = row.get("department_id")
            try:
                department_id = int(department_raw) if department_raw not in (None, "",) else None
                if department_id is not None and department_id <= 0:
                    department_id = None
            except Exception:
                department_id = None

            favorite_raw = row.get("favorite")
            favorite = False
            if isinstance(favorite_raw, str):
                favorite = favorite_raw.strip().lower() in ("true", "1", "yes", "y")

            data = {
                "name": name,
                "email": email,
                "phone": (row.get("phone") or None),
                "mobile": (row.get("mobile") or None),
                "company": (row.get("company") or None),
                "title": (row.get("title") or None),
                "department_id": department_id,
                "address": (row.get("address") or None),
                "memo": (row.get("memo") or None),
                "favorite": favorite,
                "profile_image_url": (row.get("profile_image_url") or None),
            }

            AddressBookService.create_contact(db, org_id, data)
            imported += 1

        except Exception as e:
            msg = str(e)
            # 중복 이메일/유효성 오류 등 모든 예외를 수집하고 다음 행 처리 지속
            logger.warning(f"⚠️ CSV 행 처리 실패 (row={idx}) - {msg}")
            errors.append({
                "row": idx,
                "name": row.get("name"),
                "email": row.get("email"),
                "error": msg
            })

    return {
        "success": True,
        "imported": imported,
        "failed": len(errors),
        "errors": errors
    }


# Import from organization users
@router.post("/contacts/import-from-organization", summary="조직 사용자로부터 연락처 생성")
def import_from_org(
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org_id),
    current_user: User = Depends(get_current_user)
):
    """
    현재 조직의 사용자 목록에서 이메일을 가진 사용자들을 연락처로 생성합니다.

    - 이미 존재하는 이메일은 건너뛰며, 오류는 수집하여 함께 반환합니다.
    - 이메일은 소문자/공백 제거로 정규화하여 중복을 판정합니다.
    """
    from ..model.user_model import User

    # 기존 연락처 이메일(정규화) 수집
    existing_emails = set(
        (e.strip().lower())
        for e, in db.query(Contact.email).filter(Contact.org_id == org_id, Contact.email.isnot(None)).all()
        if isinstance(e, str) and e.strip()
    )

    users = db.query(User).filter(User.org_id == org_id).all()
    created = 0
    skipped_no_email = 0
    skipped_duplicate = 0
    errors: list[dict] = []

    # 동일 실행 내 중복 방지용 (사용자 간 중복)
    seen_emails = set(existing_emails)

    for u in users:
        try:
            raw_email = getattr(u, "email", None)
            email = (raw_email.strip().lower()) if isinstance(raw_email, str) and raw_email.strip() else None
            if not email:
                skipped_no_email += 1
                continue
            if email in seen_emails:
                skipped_duplicate += 1
                continue

            data = {
                "name": getattr(u, "username", "") or "",
                "email": email,
                "company": None,
                "title": None
            }

            AddressBookService.create_contact(db, org_id, data)
            created += 1
            seen_emails.add(email)

        except Exception as e:
            msg = str(e)
            errors.append({
                "user_id": getattr(u, "id", None),
                "username": getattr(u, "username", None),
                "email": getattr(u, "email", None),
                "error": msg
            })

    return {
        "success": True,
        "created": created,
        "skipped_no_email": skipped_no_email,
        "skipped_duplicate": skipped_duplicate,
        "failed": len(errors),
        "errors": errors
    }


# 테스트용 간단한 CSV 엔드포인트 (인증 없음)
@router.get("/test-csv", summary="테스트 CSV")
def test_csv_endpoint():
    """테스트용 간단한 CSV 엔드포인트 (인증 없음)"""
    return {"message": "CSV test endpoint working"}

# 또 다른 테스트 엔드포인트
@router.get("/simple-test", summary="간단한 테스트")
def simple_test():
    """가장 간단한 테스트 엔드포인트"""
    return {"status": "ok"}


# CSV Export - 파일 끝에 위치
@router.get("/download-csv", summary="연락처 CSV 다운로드")
def download_contacts_csv(
    db: Session = Depends(get_db), 
    org_id: str = Depends(get_current_org_id),
    current_user: User = Depends(get_current_user)
):
    """
    조직의 연락처를 CSV 형식으로 다운로드합니다.
    """
    logger.info(f"📤 CSV 다운로드 시작 - 조직: {org_id}")
    
    # 연락처 조회
    contacts, _ = AddressBookService.list_contacts(db, org_id, page=1, size=100000, q=None)
    
    # CSV 생성
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "email", "phone", "mobile", "company", "title", "address"])
    
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
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contacts.csv"}
    )