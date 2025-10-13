from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict


class DepartmentOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


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