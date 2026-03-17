from typing import Any, Optional
from pydantic import BaseModel, Field

class ParsedItem(BaseModel):
    """Base for any extracted item (experience, education, etc.)"""
    metadata: dict[str, Any] = Field(default_factory=dict)

class ParsedHeader(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    website: str = ""

class ParsedExperience(ParsedItem):
    company: str = ""
    role: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    bullets: list[str] = Field(default_factory=list)

class ParsedEducation(ParsedItem):
    institution: str = ""
    degree: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    details: list[str] = Field(default_factory=list)

class ParsedProject(ParsedItem):
    name: str = ""
    tech_stack: str = ""
    url: str = ""
    bullets: list[str] = Field(default_factory=list)

class ParsedSkills(ParsedItem):
    category: str = "Skills"
    items: list[str] = Field(default_factory=list)

class ParsedSection(BaseModel):
    section_type: str  # experience, education, project, skills, generic
    title: str
    items: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = 1.0

class ResumeParseResult(BaseModel):
    header: ParsedHeader = Field(default_factory=ParsedHeader)
    sections: list[ParsedSection] = Field(default_factory=list)
    unparsed_blocks: list[str] = Field(default_factory=list)
    style_config: dict[str, Any] = Field(default_factory=dict)
