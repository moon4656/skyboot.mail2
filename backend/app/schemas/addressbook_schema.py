from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict


class DepartmentOut(BaseModel):
    """부서 응답 스키마"""
    id: int
    name: str
    parent_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class DepartmentCreate(BaseModel):
    """부서 생성 요청 스키마"""
    name: str
    parent_id: Optional[int] = None


class DepartmentUpdate(BaseModel):
    """부서 수정 요청 스키마"""
    name: Optional[str] = None
    parent_id: Optional[int] = None


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class GroupOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ContactCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    department_id: Optional[int] = None
    address: Optional[str] = None
    memo: Optional[str] = None
    favorite: Optional[bool] = False


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    department_id: Optional[int] = None
    address: Optional[str] = None
    memo: Optional[str] = None
    favorite: Optional[bool] = None


class ContactOut(BaseModel):
    contact_uuid: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    department_id: Optional[int] = None
    address: Optional[str] = None
    memo: Optional[str] = None
    favorite: bool
    profile_image_url: Optional[str] = None
    groups: List[GroupOut] = []

    model_config = ConfigDict(from_attributes=True)


class PaginatedContacts(BaseModel):
    items: List[ContactOut]
    total: int
    page: int
    size: int