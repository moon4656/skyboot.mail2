from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database.user import Base
import uuid


def generate_contact_uuid(ctx=None):
    return str(uuid.uuid4())


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(String(36), ForeignKey("organizations.org_id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    parent = relationship("Department", remote_side=[id])
    contacts = relationship("Contact", back_populates="department")

    __table_args__ = (
        UniqueConstraint('org_id', 'name', name='unique_org_department_name'),
    )


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(String(36), ForeignKey("organizations.org_id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    contacts = relationship("ContactGroup", back_populates="group", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('org_id', 'name', name='unique_org_group_name'),
    )


class Contact(Base):
    __tablename__ = "contacts"

    contact_uuid = Column(String(36), primary_key=True, index=True, default=generate_contact_uuid)
    org_id = Column(String(36), ForeignKey("organizations.org_id"), nullable=False, index=True)

    # 기본 정보
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    mobile = Column(String(50), nullable=True)
    company = Column(String(200), nullable=True)
    title = Column(String(100), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    # 기타 정보
    address = Column(Text, nullable=True)
    memo = Column(Text, nullable=True)
    favorite = Column(Boolean, default=False)
    profile_image_url = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    department = relationship("Department", back_populates="contacts")
    group_links = relationship("ContactGroup", back_populates="contact", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('org_id', 'email', name='unique_org_contact_email'),
    )


class ContactGroup(Base):
    __tablename__ = "contact_groups"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(String(36), ForeignKey("organizations.org_id"), nullable=False, index=True)
    contact_uuid = Column(String(36), ForeignKey("contacts.contact_uuid"), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    contact = relationship("Contact", back_populates="group_links")
    group = relationship("Group", back_populates="contacts")

    __table_args__ = (
        UniqueConstraint('org_id', 'contact_uuid', 'group_id', name='unique_org_contact_group'),
    )