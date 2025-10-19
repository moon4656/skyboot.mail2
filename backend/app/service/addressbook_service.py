from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from ..model.addressbook_model import Contact, Group, ContactGroup, Department


class AddressBookService:
    @staticmethod
    def list_contacts(db: Session, org_id: str, page: int = 1, size: int = 20, q: Optional[str] = None) -> Tuple[List[Contact], int]:
        query = db.query(Contact).filter(Contact.org_id == org_id)

        if q:
            like = f"%{q}%"
            query = query.filter(
                or_(
                    Contact.name.ilike(like),
                    Contact.email.ilike(like),
                    Contact.phone.ilike(like),
                    Contact.company.ilike(like),
                )
            )

        total = query.count()
        items = query.order_by(Contact.created_at.desc()).offset((page - 1) * size).limit(size).all()
        return items, total

    @staticmethod
    def get_contact(db: Session, org_id: str, contact_uuid: str) -> Optional[Contact]:
        return db.query(Contact).filter(Contact.org_id == org_id, Contact.contact_uuid == contact_uuid).first()

    @staticmethod
    def create_contact(db: Session, org_id: str, data: dict) -> Contact:
        """
        연락처를 생성합니다.
        
        Args:
            db: 데이터베이스 세션
            org_id: 조직 ID
            data: 연락처 데이터
            
        Returns:
            생성된 연락처 객체
            
        Raises:
            ValueError: 이메일 중복 또는 유효하지 않은 department_id인 경우
        """
        try:
            # department_id가 제공된 경우 유효성 검사
            if data.get('department_id'):
                from ..model.addressbook_model import Department
                dept = db.query(Department).filter(
                    Department.org_id == org_id,
                    Department.id == data['department_id']
                ).first()
                if not dept:
                    raise ValueError(f"유효하지 않은 부서 ID입니다: {data['department_id']}")
            
            # 이메일 중복 검사 (이메일이 제공된 경우)
            if data.get('email'):
                existing = db.query(Contact).filter(
                    Contact.org_id == org_id,
                    Contact.email == data['email']
                ).first()
                if existing:
                    raise ValueError(f"이미 존재하는 이메일입니다: {data['email']}")
            
            contact = Contact(org_id=org_id, **data)
            db.add(contact)
            db.commit()
            db.refresh(contact)
            return contact
            
        except Exception as e:
            db.rollback()
            # SQLAlchemy 제약 조건 오류를 사용자 친화적 메시지로 변환
            error_msg = str(e)
            if "unique_org_contact_email" in error_msg:
                raise ValueError(f"이미 존재하는 이메일입니다: {data.get('email', 'Unknown')}")
            elif "department" in error_msg.lower():
                raise ValueError(f"유효하지 않은 부서 ID입니다: {data.get('department_id', 'Unknown')}")
            else:
                raise ValueError(f"연락처 생성 중 오류가 발생했습니다: {error_msg}")

    @staticmethod
    def update_contact(db: Session, org_id: str, contact_uuid: str, data: dict) -> Optional[Contact]:
        contact = db.query(Contact).filter(Contact.org_id == org_id, Contact.contact_uuid == contact_uuid).first()
        if not contact:
            return None
        for k, v in data.items():
            setattr(contact, k, v)
        db.commit()
        db.refresh(contact)
        return contact

    @staticmethod
    def delete_contact(db: Session, org_id: str, contact_uuid: str) -> bool:
        contact = db.query(Contact).filter(Contact.org_id == org_id, Contact.contact_uuid == contact_uuid).first()
        if not contact:
            return False
        db.delete(contact)
        db.commit()
        return True

    # Groups
    @staticmethod
    def list_groups(db: Session, org_id: str) -> List[Group]:
        return db.query(Group).filter(Group.org_id == org_id).order_by(Group.name.asc()).all()

    @staticmethod
    def create_group(db: Session, org_id: str, name: str, description: Optional[str] = None) -> Group:
        """
        그룹을 생성합니다.
        
        Args:
            db: 데이터베이스 세션
            org_id: 조직 ID
            name: 그룹명
            description: 그룹 설명 (선택사항)
            
        Returns:
            생성된 그룹 객체
            
        Raises:
            ValueError: 그룹명이 중복되거나 기타 오류가 발생한 경우
        """
        try:
            # 그룹명 중복 검사
            existing = db.query(Group).filter(
                Group.org_id == org_id,
                Group.name == name
            ).first()
            if existing:
                raise ValueError(f"이미 존재하는 그룹명입니다: {name}")
            
            group = Group(org_id=org_id, name=name, description=description)
            db.add(group)
            db.commit()
            db.refresh(group)
            return group
            
        except Exception as e:
            db.rollback()
            # SQLAlchemy 제약 조건 오류를 사용자 친화적 메시지로 변환
            error_msg = str(e)
            if "unique" in error_msg.lower() and "name" in error_msg.lower():
                raise ValueError(f"이미 존재하는 그룹명입니다: {name}")
            else:
                raise ValueError(f"그룹 생성 중 오류가 발생했습니다: {error_msg}")

    @staticmethod
    def update_group(db: Session, org_id: str, group_id: int, data: dict) -> Optional[Group]:
        group = db.query(Group).filter(Group.org_id == org_id, Group.id == group_id).first()
        if not group:
            return None
        for k, v in data.items():
            setattr(group, k, v)
        db.commit()
        db.refresh(group)
        return group

    @staticmethod
    def delete_group(db: Session, org_id: str, group_id: int) -> bool:
        group = db.query(Group).filter(Group.org_id == org_id, Group.id == group_id).first()
        if not group:
            return False
        db.delete(group)
        db.commit()
        return True

    @staticmethod
    def add_contact_to_group(db: Session, org_id: str, contact_uuid: str, group_id: int) -> bool:
        contact = db.query(Contact).filter(Contact.org_id == org_id, Contact.contact_uuid == contact_uuid).first()
        group = db.query(Group).filter(Group.org_id == org_id, Group.id == group_id).first()
        if not contact or not group:
            return False
        exists = db.query(ContactGroup).filter(
            ContactGroup.org_id == org_id,
            ContactGroup.contact_uuid == contact_uuid,
            ContactGroup.group_id == group_id
        ).first()
        if exists:
            return True
        link = ContactGroup(org_id=org_id, contact_uuid=contact_uuid, group_id=group_id)
        db.add(link)
        db.commit()
        return True

    @staticmethod
    def remove_contact_from_group(db: Session, org_id: str, contact_uuid: str, group_id: int) -> bool:
        link = db.query(ContactGroup).filter(
            ContactGroup.org_id == org_id,
            ContactGroup.contact_uuid == contact_uuid,
            ContactGroup.group_id == group_id
        ).first()
        if not link:
            return False
        db.delete(link)
        db.commit()
        return True