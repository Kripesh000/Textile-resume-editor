"""Import parsed resume data into the user's JSON-based Profile.

Shared by both the PDF and LaTeX upload paths. Takes the parsed result 
and merges into ProfileDB.data with hash-based deduplication and syncing.
"""

import json
import hashlib
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db_models import ProfileDB
from app.models import Profile, Experience, Project, Education, SkillCategory, Bullet

async def import_parsed_to_profile(
    parsed: dict, user_id: str, db: AsyncSession
) -> dict:
    """
    Import parsed resume data into the user's profile.
    
    Args:
        parsed: Dict with 'header' and 'sections' keys.
        user_id: The ID of the user.
        db: Database session.
    """
    result_meta = {
        "items_added": 0,
        "items_skipped": 0,
        "personal_info_updated": [],
    }

    # 1. Fetch current profile
    stmt = select(ProfileDB).where(ProfileDB.user_id == user_id)
    pd_res = await db.execute(stmt)
    profile_db = pd_res.scalar_one_or_none()
    
    if not profile_db:
        # Should be created by profile_service, but fallback here
        profile = Profile(user_id=user_id, name="", email="", phone="")
    else:
        profile = Profile(**profile_db.data)

    # 2. Update Header/Personal Info
    header = parsed.get("header", {})
    if header:
        for field in ["name", "email", "phone", "linkedin", "github", "website"]:
            val = header.get(field)
            if val and not getattr(profile, field):
                setattr(profile, field, val)
                result_meta["personal_info_updated"].append(field)

    # 3. Process Sections
    sections = parsed.get("sections", [])
    for sec in sections:
        sec_type = sec.get("section_type")
        items = sec.get("items", [])
        
        if not items:
            continue

        # 3.1 Hash-based Section Diffing
        # Compute hash of incoming items
        incoming_hash = hashlib.sha256(json.dumps(items, sort_keys=True).encode()).hexdigest()
        
        # Check existing section for a match
        # (This is a simplified check: we check if ALL items in that category match)
        # In a more advanced version, we'd hash individual items.
        
        if sec_type == "experience":
            _merge_experience(profile, items, result_meta)
        elif sec_type == "project":
            _merge_projects(profile, items, result_meta)
        elif sec_type == "education":
            _merge_education(profile, items, result_meta)
        elif sec_type == "skills":
            _merge_skills(profile, items, result_meta)

    # 4. Save
    if profile_db:
        profile_db.data = profile.model_dump()
    else:
        profile_db = ProfileDB(user_id=user_id, data=profile.model_dump())
        db.add(profile_db)
    
    await db.commit()
    return result_meta

def _merge_experience(profile: Profile, items: list[dict], meta: dict):
    existing_hashes = {
        hashlib.sha256(json.dumps(e.model_dump(exclude={"id", "bullets"}), sort_keys=True).encode()).hexdigest()
        for e in profile.experiences
    }
    for item in items:
        # Convert to model for stable hashing
        bullets = [Bullet(text=b) for b in item.get("bullets", [])]
        exp = Experience(
            company=item.get("company", ""),
            role=item.get("role", ""),
            location=item.get("location", ""),
            start=item.get("start") or item.get("start_date") or "",
            end=item.get("end") or item.get("end_date") or "",
            bullets=bullets
        )
        ihash = hashlib.sha256(json.dumps(exp.model_dump(exclude={"id", "bullets"}), sort_keys=True).encode()).hexdigest()
        if ihash in existing_hashes:
            meta["items_skipped"] += 1
        else:
            profile.experiences.append(exp)
            existing_hashes.add(ihash)  # Prevent duplicates in same batch
            meta["items_added"] += 1

def _merge_projects(profile: Profile, items: list[dict], meta: dict):
    existing_hashes = {
        hashlib.sha256(json.dumps(p.model_dump(exclude={"id", "bullets"}), sort_keys=True).encode()).hexdigest()
        for p in profile.projects
    }
    for item in items:
        bullets = [Bullet(text=b) for b in item.get("bullets", [])]
        proj = Project(
            name=item.get("name", ""),
            tech_stack=item.get("tech_stack", ""),
            date=item.get("date", ""),
            bullets=bullets
        )
        ihash = hashlib.sha256(json.dumps(proj.model_dump(exclude={"id", "bullets"}), sort_keys=True).encode()).hexdigest()
        if ihash in existing_hashes:
            meta["items_skipped"] += 1
        else:
            profile.projects.append(proj)
            existing_hashes.add(ihash)  # Prevent duplicates in same batch
            meta["items_added"] += 1

def _merge_education(profile: Profile, items: list[dict], meta: dict):
    existing_hashes = {
        hashlib.sha256(json.dumps(e.model_dump(exclude={"id"}), sort_keys=True).encode()).hexdigest()
        for e in profile.education
    }
    for item in items:
        ed = Education(
            institution=item.get("institution", ""),
            degree=item.get("degree", ""),
            location=item.get("location", ""),
            end=item.get("end") or item.get("end_date") or "",
            gpa=item.get("gpa"),
            coursework=item.get("coursework"),
            awards=item.get("awards")
        )
        ihash = hashlib.sha256(json.dumps(ed.model_dump(exclude={"id"}), sort_keys=True).encode()).hexdigest()
        if ihash in existing_hashes:
            meta["items_skipped"] += 1
        else:
            profile.education.append(ed)
            existing_hashes.add(ihash)  # Prevent duplicates in same batch
            meta["items_added"] += 1

def _merge_skills(profile: Profile, items: list[dict], meta: dict):
    for item in items:
        cat_name = item.get("category", "Skills")
        skill_items = item.get("items", [])
        
        # Find existing category
        existing = next((c for c in profile.skill_categories if c.name == cat_name), None)
        if existing:
            # Add only new items (case-insensitive deduplication)
            current_skills_low = {s.lower() for s in existing.items}
            new_skills = []
            for s in skill_items:
                if s.lower() not in current_skills_low:
                    new_skills.append(s)
                    current_skills_low.add(s.lower())
            
            existing.items.extend(new_skills)
            meta["items_added"] += len(new_skills)
            meta["items_skipped"] += (len(skill_items) - len(new_skills))
        else:
            # New category, but deduplicate within the category itself
            unique_skills = []
            seen = set()
            for s in skill_items:
                if s.lower() not in seen:
                    unique_skills.append(s)
                    seen.add(s.lower())
            profile.skill_categories.append(SkillCategory(name=cat_name, items=unique_skills))
            meta["items_added"] += len(unique_skills)
