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
        contact = Contact(org_id=org_id, **data)
        db.add(contact)
        db.commit()
        db.refresh(contact)
        return contact

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
        group = Group(org_id=org_id, name=name, description=description)
        db.add(group)
        db.commit()
        db.refresh(group)
        return group

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