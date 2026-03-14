from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SectionCreate(BaseModel):
    section_type: str
    title: str
    order_index: int = 0
    items: list[Any] = []


class SectionUpdate(BaseModel):
    title: str | None = None
    items: list[Any] | None = None


class SectionReorderItem(BaseModel):
    section_id: str
    order_index: int


class SectionResponse(BaseModel):
    id: str
    resume_id: str
    section_type: str
    title: str
    order_index: int
    items: list[Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResumeCreate(BaseModel):
    title: str = "Untitled Resume"
    template_key: str = "classic"


class ResumeUpdate(BaseModel):
    title: str | None = None
    template_key: str | None = None
    template_config: dict | None = None
    header_data: dict | None = None


class ResumeResponse(BaseModel):
    id: str
    user_id: str
    title: str
    template_key: str
    template_config: dict | None = None
    header_data: dict
    sections: list[SectionResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResumeListItem(BaseModel):
    id: str
    title: str
    template_key: str
    template_config: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
