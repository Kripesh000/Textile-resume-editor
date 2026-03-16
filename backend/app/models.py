# app/models.py — the frozen public contract
from pydantic import BaseModel
from typing import Optional
import uuid

# ── Atomic pieces ──────────────────────────────────────────

class Bullet(BaseModel):
    id: str = uuid.uuid4().hex
    text: str
    tags: list[str] = []
    order: int = 0                    # for reordering within a parent

class Experience(BaseModel):
    id: str = uuid.uuid4().hex
    company: str
    role: str
    location: str
    start: str
    end: str
    tags: list[str] = []
    bullets: list[Bullet] = []

class Project(BaseModel):
    id: str = uuid.uuid4().hex
    name: str
    tech_stack: str
    date: str
    tags: list[str] = []
    bullets: list[Bullet] = []

class Education(BaseModel):
    id: str = uuid.uuid4().hex
    institution: str
    degree: str
    location: str
    end: str
    gpa: Optional[str] = None
    coursework: Optional[str] = None
    awards: Optional[str] = None

class SkillCategory(BaseModel):
    id: str = uuid.uuid4().hex
    name: str                         # "Languages", "Frameworks"
    items: list[str] = []
    tags: list[str] = []

# ── Profile (source of truth) ──────────────────────────────

class Profile(BaseModel):
    user_id: str
    name: str
    email: str
    phone: str
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None
    experiences: list[Experience] = []
    projects: list[Project] = []
    education: list[Education] = []
    skill_categories: list[SkillCategory] = []

# ── Variant (a resume = a query over the profile) ──────────

class SectionConfig(BaseModel):
    title: str
    order: int

class ResumeVariant(BaseModel):
    id: str = uuid.uuid4().hex
    user_id: str
    name: str                         # "Amazon SDE 2025", "DS - Google"
    template_id: str
    selected_experience_ids: list[str] = []
    selected_project_ids: list[str] = []
    selected_bullet_ids: list[str] = []  # bullet-level granularity
    selected_skill_category_ids: list[str] = []
    section_order: list[SectionConfig] = []
    created_at: str
    updated_at: str

# ── Template config (what each template declares) ──────────

class TemplateSupports(BaseModel):
    summary: bool = False
    photo: bool = False
    color_accent: bool = False
    two_column_skills: bool = False

class TemplateConfig(BaseModel):
    id: str
    name: str
    tags: list[str]                   # ["ats-safe", "traditional", "modern"]
    max_experiences: int = 4
    max_projects: int = 4
    max_skill_categories: int = 4
    supports: TemplateSupports = TemplateSupports()
    section_order_locked: bool = False
    required_sections: list[str] = ["Education", "Experience"]
