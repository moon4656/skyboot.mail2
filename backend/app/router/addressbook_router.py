from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import csv
import io

from ..database.user import get_db
from ..middleware.tenant_middleware import get_current_org_id
from ..service.addressbook_service import AddressBookService
from ..schemas.addressbook_schema import (
    ContactCreate, ContactUpdate, ContactOut, PaginatedContacts,
    GroupCreate, GroupUpdate, GroupOut
)

router = APIRouter()


@router.get("/contacts", response_model=PaginatedContacts, summary="연락처 목록 조회")
def list_contacts(
    page: int = 1,
    size: int = 20,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org_id)
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
    org_id: str = Depends(get_current_org_id)
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


@router.get("/contacts/{contact_uuid}", response_model=ContactOut, summary="연락처 상세 조회")
def get_contact(contact_uuid: str, db: Session = Depends(get_db), org_id: str = Depends(get_current_org_id)):
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
def update_contact(contact_uuid: str, body: ContactUpdate, db: Session = Depends(get_db), org_id: str = Depends(get_current_org_id)):
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


@router.delete("/contacts/{contact_uuid}", summary="연락처 삭제")
def delete_contact(contact_uuid: str, db: Session = Depends(get_db), org_id: str = Depends(get_current_org_id)):
    ok = AddressBookService.delete_contact(db, org_id, contact_uuid)
    if not ok:
        raise HTTPException(status_code=404, detail="연락처를 찾을 수 없습니다")
    return {"success": True}


# Groups
@router.get("/groups", response_model=list[GroupOut], summary="그룹 목록 조회")
def list_groups(db: Session = Depends(get_db), org_id: str = Depends(get_current_org_id)):
    groups = AddressBookService.list_groups(db, org_id)
    return [GroupOut.from_orm(g) for g in groups]


@router.post("/groups", response_model=GroupOut, summary="그룹 생성")
def create_group(body: GroupCreate, db: Session = Depends(get_db), org_id: str = Depends(get_current_org_id)):
    group = AddressBookService.create_group(db, org_id, body.name, body.description)
    return GroupOut.from_orm(group)


@router.put("/groups/{group_id}", response_model=GroupOut, summary="그룹 수정")
def update_group(group_id: int, body: GroupUpdate, db: Session = Depends(get_db), org_id: str = Depends(get_current_org_id)):
    group = AddressBookService.update_group(db, org_id, group_id, body.dict(exclude_unset=True))
    if not group:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다")
    return GroupOut.from_orm(group)


@router.delete("/groups/{group_id}", summary="그룹 삭제")
def delete_group(group_id: int, db: Session = Depends(get_db), org_id: str = Depends(get_current_org_id)):
    ok = AddressBookService.delete_group(db, org_id, group_id)
    if not ok:
        raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다")
    return {"success": True}


@router.post("/contacts/{contact_uuid}/groups/{group_id}", summary="연락처를 그룹에 추가")
def add_to_group(contact_uuid: str, group_id: int, db: Session = Depends(get_db), org_id: str = Depends(get_current_org_id)):
    ok = AddressBookService.add_contact_to_group(db, org_id, contact_uuid, group_id)
    if not ok:
        raise HTTPException(status_code=404, detail="연락처/그룹을 찾을 수 없습니다")
    return {"success": True}


@router.delete("/contacts/{contact_uuid}/groups/{group_id}", summary="연락처를 그룹에서 제거")
def remove_from_group(contact_uuid: str, group_id: int, db: Session = Depends(get_db), org_id: str = Depends(get_current_org_id)):
    ok = AddressBookService.remove_contact_from_group(db, org_id, contact_uuid, group_id)
    if not ok:
        raise HTTPException(status_code=404, detail="연락처/그룹 링크를 찾을 수 없습니다")
    return {"success": True}


# CSV Export/Import
@router.get("/contacts/export", summary="연락처 CSV 내보내기")
def export_contacts(db: Session = Depends(get_db), org_id: str = Depends(get_current_org_id)):
    items, _ = AddressBookService.list_contacts(db, org_id, page=1, size=100000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "email", "phone", "mobile", "company", "title", "address"])
    for c in items:
        writer.writerow([c.name or "", c.email or "", c.phone or "", c.mobile or "", c.company or "", c.title or "", (c.address or "").replace('\n',' ')])
    csv_text = output.getvalue()
    return {"content_type": "text/csv", "data": csv_text}


@router.post("/contacts/import", summary="연락처 CSV 가져오기")
async def import_contacts(file: UploadFile = File(...), db: Session = Depends(get_db), org_id: str = Depends(get_current_org_id)):
    content = await file.read()
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    count = 0
    for row in reader:
        data = {
            "name": row.get("name") or "",
            "email": row.get("email") or None,
            "phone": row.get("phone") or None,
            "mobile": row.get("mobile") or None,
            "company": row.get("company") or None,
            "title": row.get("title") or None,
            "address": row.get("address") or None,
        }
        AddressBookService.create_contact(db, org_id, data)
        count += 1
    return {"success": True, "imported": count}


# Import from organization users
@router.post("/contacts/import-from-organization", summary="조직 사용자로부터 연락처 생성")
def import_from_org(db: Session = Depends(get_db), org_id: str = Depends(get_current_org_id)):
    from ..model.user_model import User
    existing_emails = set(
        e for e, in db.query(Contact.email).filter(Contact.org_id == org_id, Contact.email.isnot(None)).all()
    )
    users = db.query(User).filter(User.org_id == org_id).all()
    created = 0
    for u in users:
        email = u.email
        if email and email not in existing_emails:
            AddressBookService.create_contact(db, org_id, {
                "name": u.username,
                "email": u.email,
                "company": None,
                "title": None
            })
            created += 1
    return {"success": True, "created": created}