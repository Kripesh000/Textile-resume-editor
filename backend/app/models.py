from pydantic import BaseModel, Field
from typing import Optional
import uuid

def gen_id():
    return uuid.uuid4().hex

# ── Atomic pieces ──────────────────────────────────────────

class Bullet(BaseModel):
    id: str = Field(default_factory=gen_id)
    text: str
    tags: list[str] = []
    order: int = 0                    # for reordering within a parent

class Experience(BaseModel):
    id: str = Field(default_factory=gen_id)
    company: str
    role: str
    location: str
    start: str
    end: str
    tags: list[str] = []
    bullets: list[Bullet] = []

class Project(BaseModel):
    id: str = Field(default_factory=gen_id)
    name: str
    tech_stack: str
    date: str
    tags: list[str] = []
    bullets: list[Bullet] = []

class Education(BaseModel):
    id: str = Field(default_factory=gen_id)
    institution: str
    degree: str
    location: str
    end: str
    gpa: Optional[str] = None
    coursework: Optional[str] = None
    awards: Optional[str] = None

class SkillCategory(BaseModel):
    id: str = Field(default_factory=gen_id)
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
    id: str = Field(default_factory=gen_id)
    user_id: Optional[str] = None
    profile_id: Optional[str] = None
    name: Optional[str] = "Untitled Resume"
    template_id: Optional[str] = "jake_classic"
    selected_experience_ids: list[str] = []
    selected_project_ids: list[str] = []
    selected_bullet_ids: list[str] = []  # bullet-level granularity
    selected_skill_category_ids: list[str] = []
    section_order: list[SectionConfig] = []
    # Legacy/Extended fields
    header_data: Optional[dict] = None
    sections: Optional[list] = None
    template_config: Optional[dict] = None  # Principle #7
    raw_latex: Optional[str] = None         # Principle #7
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

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
