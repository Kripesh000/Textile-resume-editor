from datetime import datetime
from typing import Any

from pydantic import BaseModel


# --- Profile Items ---

class ProfileItemCreate(BaseModel):
    data: dict[str, Any] = {}
    order_index: int = 0


class ProfileItemUpdate(BaseModel):
    data: dict[str, Any] | None = None
    order_index: int | None = None


class ProfileItemResponse(BaseModel):
    id: str
    section_id: str
    order_index: int
    data: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Profile Sections ---

class ProfileSectionCreate(BaseModel):
    section_type: str
    title: str
    order_index: int = 0


class ProfileSectionUpdate(BaseModel):
    title: str | None = None
    order_index: int | None = None


class ProfileSectionResponse(BaseModel):
    id: str
    user_id: str
    section_type: str
    title: str
    order_index: int
    items: list[ProfileItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Personal Info (stored on User or as header-like data) ---

class PersonalInfoUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin: str | None = None
    github: str | None = None
    website: str | None = None


class PersonalInfoResponse(BaseModel):
    name: str
    email: str
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    website: str = ""


class ProfileResponse(BaseModel):
    personal_info: PersonalInfoResponse
    sections: list[ProfileSectionResponse] = []
