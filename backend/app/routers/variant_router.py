import datetime
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.db_models import UserDB, ProfileDB, ResumeVariantDB
from app.models import Profile, ResumeVariant, SectionConfig
from app.services.auth_service import get_current_user
from app.services.resume_service import build_render_data
from app.services.latex_service import render_template, compile_pdf

router = APIRouter(prefix="/api/v1/variants", tags=["variants"])

@router.get("", response_model=list[ResumeVariant])
async def list_variants(
    user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResumeVariantDB).where(ResumeVariantDB.user_id == user.id)
    )
    dbs = result.scalars().all()
    
    # Fetch Profile for expansion
    result = await db.execute(select(ProfileDB).where(ProfileDB.user_id == user.id))
    profile_db = result.scalar_one_or_none()
    profile = Profile(**profile_db.data) if profile_db else None

    variants = []
    for db_item in dbs:
        data = db_item.data
        if profile:
            expanded = build_render_data(profile, ResumeVariant(**data), {})
            data["header_data"] = expanded["header_data"]
            data["sections"] = expanded["sections"]
            # Map legacy section structure (entries -> items) if needed by component
            for s in data["sections"]:
                s["items"] = s.get("entries", [])
                s["id"] = f"section-{s['type']}"
                s["id"] = f"section-{s['type']}"
        variants.append(ResumeVariant(**data))
    return variants


@router.post("", response_model=ResumeVariant)
async def create_variant(
    variant: ResumeVariant,
    user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    variant.user_id = user.id
    
    # Ensure profile_id
    if not variant.profile_id:
        result = await db.execute(select(ProfileDB).where(ProfileDB.user_id == user.id))
        profile_db = result.scalar_one_or_none()
        if not profile_db:
            # Create a blank profile if it doesn't exist
            profile_db = ProfileDB(user_id=user.id, data=Profile(user_id=user.id, name=user.name, email=user.email, phone="").model_dump())
            db.add(profile_db)
            await db.flush()
        variant.profile_id = profile_db.id

    # If new variant, select all items by default for better UX in legacy editor
    if not variant.selected_experience_ids and not variant.selected_project_ids:
        result = await db.execute(select(ProfileDB).where(ProfileDB.id == variant.profile_id))
        p_db = result.scalar_one_or_none()
        if p_db:
            p = Profile(**p_db.data)
            variant.selected_experience_ids = [e.id for e in p.experiences]
            variant.selected_project_ids = [p_proj.id for p_proj in p.projects]
            variant.selected_skill_category_ids = [s.id for s in p.skill_categories]
            variant.selected_bullet_ids = []
            for e in p.experiences: variant.selected_bullet_ids.extend([b.id for b in e.bullets])
            for pj in p.projects: variant.selected_bullet_ids.extend([b.id for b in pj.bullets])
            variant.section_order = [
                SectionConfig(title="Experience", order=0),
                SectionConfig(title="Projects", order=1),
                SectionConfig(title="Education", order=2),
                SectionConfig(title="Skills", order=3),
            ]

    # Create DB entry
    variant_db = ResumeVariantDB(
        id=variant.id,
        user_id=user.id,
        profile_id=variant.profile_id,
        template_id=variant.template_id or "jake_classic",
        name=variant.name or "New Resume",
        data=variant.model_dump()
    )
    db.add(variant_db)
    await db.commit()
    await db.refresh(variant_db)
    return variant


@router.get("/{variant_id}", response_model=ResumeVariant)
async def get_variant(
    variant_id: str,
    user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResumeVariantDB).where(ResumeVariantDB.id == variant_id, ResumeVariantDB.user_id == user.id)
    )
    variant_db = result.scalar_one_or_none()
    if not variant_db:
        raise HTTPException(status_code=404, detail="Variant not found")
    
    data = variant_db.data
    
    # Fetch Profile for expansion
    result = await db.execute(select(ProfileDB).where(ProfileDB.user_id == user.id))
    profile_db = result.scalar_one_or_none()
    if profile_db:
        profile = Profile(**profile_db.data)
        expanded = build_render_data(profile, ResumeVariant(**data), {})
        data["header_data"] = expanded["header_data"]
        data["sections"] = expanded["sections"]
        # Map legacy section structure (entries -> items)
        for idx, s in enumerate(data["sections"]):
            if "id" not in s: s["id"] = s.get("title", f"section-{idx}")
            # Send items as flat objects, not nested under {"data": ...}
            s["items"] = s.get("entries", [])
            if "section_type" not in s: s["section_type"] = s.get("type", "generic")

    data["created_at"] = variant_db.created_at.isoformat()
    data["updated_at"] = variant_db.updated_at.isoformat()
    return ResumeVariant(**data)


@router.put("/{variant_id}", response_model=ResumeVariant)
async def update_variant(
    variant_id: str,
    variant_update: ResumeVariant,
    user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResumeVariantDB).where(ResumeVariantDB.id == variant_id, ResumeVariantDB.user_id == user.id)
    )
    variant_db = result.scalar_one_or_none()
    if not variant_db:
        raise HTTPException(status_code=404, detail="Variant not found")
    
    # Merge incoming data into existing blob instead of replacing wholesale.
    # This prevents partial updates (e.g. just header_data) from wiping
    # out selections, sections, and other critical variant data.
    existing_data = dict(variant_db.data)
    incoming = variant_update.model_dump(exclude_unset=True)
    incoming["id"] = variant_id
    incoming["user_id"] = user.id
    
    # Sync section order based on explicit UI list (so deleted sections don't fall back to defaults)
    if "sections" in incoming:
        new_order = [{"title": s.get("title", ""), "order": i} for i, s in enumerate(incoming["sections"]) if s.get("title")]
        existing_data["section_order"] = new_order
        
    existing_data.update(incoming)

    variant_db.template_id = existing_data.get("template_id", variant_db.template_id)
    variant_db.name = existing_data.get("name", variant_db.name)
    variant_db.data = existing_data
    await db.commit()
    await db.refresh(variant_db)
    
    data = variant_db.data
    data["created_at"] = variant_db.created_at.isoformat()
    data["updated_at"] = variant_db.updated_at.isoformat()
    return ResumeVariant(**data)


@router.post("/{variant_id}/sections")
async def create_section(
    variant_id: str,
    data: dict,
    user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResumeVariantDB).where(ResumeVariantDB.id == variant_id, ResumeVariantDB.user_id == user.id)
    )
    variant_db = result.scalar_one_or_none()
    if not variant_db:
        raise HTTPException(status_code=404, detail="Variant not found")
    
    variant_data = variant_db.data
    sections = variant_data.get("sections", [])
    
    import uuid
    new_section = {
        "id": f"section-{uuid.uuid4().hex[:8]}",
        "section_type": data.get("section_type", "generic"),
        "title": data.get("title", "New Section"),
        "order_index": data.get("order_index", len(sections)),
        "items": []
    }
    sections.append(new_section)
    variant_data["sections"] = sections
    variant_db.data = variant_data
    variant_db.updated_at = datetime.datetime.now(datetime.UTC)
    await db.commit()
    return new_section

@router.put("/{variant_id}/sections/{section_id}")
async def update_section(
    variant_id: str,
    section_id: str,
    data: dict,
    user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResumeVariantDB).where(ResumeVariantDB.id == variant_id, ResumeVariantDB.user_id == user.id)
    )
    variant_db = result.scalar_one_or_none()
    if not variant_db:
        raise HTTPException(status_code=404, detail="Variant not found")
    
    variant_data = variant_db.data
    sections = variant_data.get("sections") or []
    
    # Update the specific section in the blob
    updated = False
    for s in sections:
        if s.get("id") == section_id or s.get("title") == section_id:
            s.update(data)
            updated = True
            break
            
    if not updated:
        # If section is not found in explicit overrides, it means the user is editing 
        # a default Profile section for the first time. We auto-generate the override.
        new_override = {
            "id": section_id,
            "title": section_id,
        }
        new_override.update(data)
        sections.append(new_override)
        updated = True
        
    variant_data["sections"] = sections
    
    if updated:
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(variant_db, "data")
        variant_db.updated_at = datetime.datetime.now(datetime.UTC)
        await db.commit()
    
    return {"status": "success"}

@router.delete("/{variant_id}")
async def delete_variant(
    variant_id: str,
    user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResumeVariantDB).where(ResumeVariantDB.id == variant_id, ResumeVariantDB.user_id == user.id)
    )
    variant_db = result.scalar_one_or_none()
    if not variant_db:
        raise HTTPException(status_code=404, detail="Variant not found")
    
    await db.delete(variant_db)
    await db.commit()
    return {"status": "deleted"}


@router.post("/{variant_id}/reorder")
async def reorder_sections(
    variant_id: str,
    data: list[dict], # list of {section_id: str, order_index: int}
    user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResumeVariantDB).where(ResumeVariantDB.id == variant_id, ResumeVariantDB.user_id == user.id)
    )
    variant_db = result.scalar_one_or_none()
    if not variant_db:
        raise HTTPException(status_code=404, detail="Variant not found")
    
    variant_data = variant_db.data
    # Create lookup for titles from overrides
    sections = variant_data.get("sections", [])
    override_titles = {s.get("id"): s.get("title") for s in sections if s.get("id")}
    
    # Sync section order based on the full list of IDs sent from UI
    # This ensures default profile sections (which aren't in 'sections' overrides) are also reordered.
    new_order = []
    for item in sorted(data, key=lambda x: x.get("order_index", 0)):
        sid = item.get("section_id")
        title = override_titles.get(sid, sid) # Fallback to sid as title for defaults
        if title:
            new_order.append({"title": title, "order": item.get("order_index", 0)})
            
    variant_data["section_order"] = new_order
    
    # Also update order_index in explicit overrides if they were moved
    order_map = {item["section_id"]: item["order_index"] for item in data}
    for s in sections:
        if s.get("id") in order_map:
            s["order_index"] = order_map[s["id"]]
    variant_data["sections"] = sections
    
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(variant_db, "data")
    variant_db.updated_at = datetime.datetime.now(datetime.UTC)
    await db.commit()
    return {"status": "success"}

@router.delete("/{variant_id}/sections/{section_id}")
async def delete_section(
    variant_id: str,
    section_id: str,
    user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResumeVariantDB).where(ResumeVariantDB.id == variant_id, ResumeVariantDB.user_id == user.id)
    )
    variant_db = result.scalar_one_or_none()
    if not variant_db:
        raise HTTPException(status_code=404, detail="Variant not found")
    
    variant_data = variant_db.data
    sections = variant_data.get("sections", [])
    variant_data["sections"] = [s for s in sections if s["id"] != section_id]
    
    variant_db.data = variant_data
    variant_db.updated_at = datetime.datetime.now(datetime.UTC)
    await db.commit()
    return {"status": "success"}

@router.post("/{variant_id}/import")
async def import_to_variant(
    variant_id: str,
    item_ids: list[str],
    user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResumeVariantDB).where(ResumeVariantDB.id == variant_id, ResumeVariantDB.user_id == user.id)
    )
    variant_db = result.scalar_one_or_none()
    if not variant_db:
        raise HTTPException(status_code=404, detail="Variant not found")
    
    # Fetch Profile to identify which category each ID belongs to
    profile_result = await db.execute(select(ProfileDB).where(ProfileDB.user_id == user.id))
    profile_db = profile_result.scalar_one_or_none()
    if not profile_db:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile = Profile(**profile_db.data)
    variant = ResumeVariant(**variant_db.data)
    
    for item_id in item_ids:
        # Check experiences
        if any(e.id == item_id for e in profile.experiences):
            if item_id not in variant.selected_experience_ids:
                variant.selected_experience_ids.append(item_id)
                exp = next(e for e in profile.experiences if e.id == item_id)
                for b in exp.bullets:
                    if b.id not in variant.selected_bullet_ids:
                        variant.selected_bullet_ids.append(b.id)
                        
            # Ensure it's in the UI overrides
            exp = next(e for e in profile.experiences if e.id == item_id)
            if variant.sections is not None:
                found_sec = next((s for s in variant.sections if s.get("section_type") == "experience" or s.get("title") == "Experience"), None)
                if not found_sec:
                    found_sec = {"id": "Experience", "title": "Experience", "section_type": "experience", "items": []}
                    variant.sections.append(found_sec)
                    from app.models import SectionConfig
                    if variant.section_order is None: variant.section_order = []
                    if not any(o.title == "Experience" for o in variant.section_order):
                        variant.section_order.append(SectionConfig(title="Experience", order=len(variant.section_order)))
                items = found_sec.get("items", found_sec.get("entries", []))
                if not any(i.get("id") == item_id for i in items):
                    items.append(exp.model_dump())
                found_sec["items"] = items
        # Check projects
        elif any(p.id == item_id for p in profile.projects):
            if item_id not in variant.selected_project_ids:
                variant.selected_project_ids.append(item_id)
                proj = next(p for p in profile.projects if p.id == item_id)
                for b in proj.bullets:
                    if b.id not in variant.selected_bullet_ids:
                        variant.selected_bullet_ids.append(b.id)
                        
            proj = next(p for p in profile.projects if p.id == item_id)
            if variant.sections is not None:
                found_sec = next((s for s in variant.sections if s.get("section_type") == "projects" or s.get("title") == "Projects"), None)
                if not found_sec:
                    found_sec = {"id": "Projects", "title": "Projects", "section_type": "projects", "items": []}
                    variant.sections.append(found_sec)
                    from app.models import SectionConfig
                    if variant.section_order is None: variant.section_order = []
                    if not any(o.title == "Projects" for o in variant.section_order):
                        variant.section_order.append(SectionConfig(title="Projects", order=len(variant.section_order)))
                items = found_sec.get("items", found_sec.get("entries", []))
                if not any(i.get("id") == item_id for i in items):
                    items.append(proj.model_dump())
                found_sec["items"] = items
        # Check education
        elif any(ed.id == item_id for ed in profile.education):
            ed = next(e for e in profile.education if e.id == item_id)
            if variant.sections is not None:
                found_sec = next((s for s in variant.sections if s.get("section_type") == "education" or s.get("title") == "Education"), None)
                if not found_sec:
                    found_sec = {"id": "Education", "title": "Education", "section_type": "education", "items": []}
                    variant.sections.append(found_sec)
                    from app.models import SectionConfig
                    if variant.section_order is None: variant.section_order = []
                    if not any(o.title == "Education" for o in variant.section_order):
                        variant.section_order.append(SectionConfig(title="Education", order=len(variant.section_order)))
                items = found_sec.get("items", found_sec.get("entries", []))
                if not any(i.get("id") == item_id for i in items):
                    items.append(ed.model_dump())
                found_sec["items"] = items
        # Check skills
        elif any(skill.id == item_id for skill in profile.skill_categories):
            if item_id not in variant.selected_skill_category_ids:
                variant.selected_skill_category_ids.append(item_id)
            skill = next(sk for sk in profile.skill_categories if sk.id == item_id)
            
            if variant.sections is not None:
                found_sec = next((s for s in variant.sections if s.get("section_type") == "skills" or s.get("title") == "Skills"), None)
                if not found_sec:
                    found_sec = {"id": "Skills", "title": "Skills", "section_type": "skills", "items": []}
                    variant.sections.append(found_sec)
                    from app.models import SectionConfig
                    if variant.section_order is None: variant.section_order = []
                    if not any(o.title == "Skills" for o in variant.section_order):
                        variant.section_order.append(SectionConfig(title="Skills", order=len(variant.section_order)))
                items = found_sec.get("items", found_sec.get("entries", []))
                if not any(i.get("id") == item_id for i in items):
                    items.append(skill.model_dump())
                found_sec["items"] = items
    
    variant_db.data = variant.model_dump()
    variant_db.updated_at = datetime.datetime.now(datetime.UTC)
    await db.commit()
    await db.refresh(variant_db)
    return variant_db.data


@router.post("/{variant_id}/render")
async def render_variant(
    variant_id: str,
    user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Fetch Variant
    result = await db.execute(
        select(ResumeVariantDB).where(ResumeVariantDB.id == variant_id, ResumeVariantDB.user_id == user.id)
    )
    variant_db = result.scalar_one_or_none()
    if not variant_db:
        raise HTTPException(status_code=404, detail="Variant not found")
        
    variant = ResumeVariant(**variant_db.data)

    # Fetch Profile
    result = await db.execute(
        select(ProfileDB).where(ProfileDB.user_id == user.id)
    )
    profile_db = result.scalar_one_or_none()
    if not profile_db:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    profile = Profile(**profile_db.data)

    # For MVP, default template config is empty
    template_config = variant.template_config or {} 

    try:
        # Build the render dictionary
        render_data = build_render_data(profile, variant, template_config)

        # ── Lazy Template Generation (Principle #7) ──
        if variant.template_id.startswith("user_"):
            # Check if template file exists
            from app.services.latex_parser_service import generate_jinja_template
            
            templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
            template_path = os.path.join(templates_dir, f"{variant.template_id}.tex.j2")
            
            if not os.path.exists(template_path):
                # Try to get raw_latex from variant data
                raw_latex = variant_db.data.get("raw_latex")
                if raw_latex:
                    # Generate and save template lazily
                    os.makedirs(os.path.dirname(template_path), exist_ok=True)
                    template_content = generate_jinja_template(raw_latex, render_data)
                    with open(template_path, "w") as f:
                        f.write(template_content)
                else:
                    raise HTTPException(status_code=400, detail=f"Custom template '{variant.template_id}' not found and no raw source available")

        # Render template to TeX
        try:
            tex_content = render_template(variant.template_id, render_data)
        except Exception as e:
            print(f"Jinja rendering error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to render LaTeX template: {str(e)}")

        # Compile TeX to PDF
        try:
            pdf_bytes = await compile_pdf(tex_content)
        except RuntimeError as e:
            print(f"Latex compilation error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Latex compilation failed: {str(e)}")

        # Return PDF response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{variant.name}.pdf"',
            },
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal render error: {str(e)}")
