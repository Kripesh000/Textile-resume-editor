from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
import io
import pdfplumber

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.db_models import UserDB
from app.models import Profile
from app.services.auth_service import get_current_user
from app.services.profile_service import get_profile as svc_get_profile, update_profile as svc_update_profile
from app.services.import_service import parse_resume_to_profile

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])

@router.get("", response_model=Profile)
async def get_profile(
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await svc_get_profile(db, current_user.id)

@router.put("", response_model=Profile)
async def update_profile(
    data: Profile,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot update another user's profile")
    return await svc_update_profile(db, current_user.id, data)

@router.post("/import", response_model=Profile)
async def import_resume(
    file: UploadFile = File(...),
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stateless parse-and-merge workflow (Principles #1-#8)."""
    filename = file.filename or ""
    content = await file.read()
    
    # 1. Parse using robust stateless parsers
    parsed = {}
    is_latex = False
    if filename.lower().endswith(".pdf") or file.content_type == "application/pdf":
        from app.services.pdf_parser_service import parse_pdf
        parsed = await parse_pdf(content)
    elif filename.lower().endswith(".tex"):
        from app.services.latex_parser_service import parse_latex
        is_latex = True
        parsed = await parse_latex(content.decode("utf-8", errors="replace"))
    else:
        raise HTTPException(status_code=400, detail="Only .pdf and .tex files are supported")

    # 2. Import parsed data into profile with hash-based diffing
    from app.services.profile_import_service import import_parsed_to_profile
    import_result = await import_parsed_to_profile(parsed, current_user.id, db)
    
    # 3. For LaTeX, create a ResumeVariant for lazy template generation
    if is_latex:
        import uuid
        from app.db_models import ResumeVariantDB
        from app.models import ResumeVariant
        
        variant_id = f"var_{uuid.uuid4().hex[:8]}"
        template_id = f"user_{variant_id}"
        
        # Note: We store raw_latex in the data blob for lazy generation (Principle #7)
        variant_data = ResumeVariant(
            id=variant_id,
            user_id=current_user.id,
            name=f"Imported: {filename}",
            template_id=template_id
        ).model_dump()
        variant_data["raw_latex"] = parsed.get("raw_source")
        
        variant_db = ResumeVariantDB(
            id=variant_id,
            user_id=current_user.id,
            profile_id=current_user.id, # We assume profile id matches user id for now in V1
            template_id=template_id,
            name=f"Imported: {filename}",
            data=variant_data
        )
        db.add(variant_db)
        await db.commit()

    return await svc_get_profile(db, current_user.id)
@router.patch("/experiences/{exp_id}/bullets/{bullet_id}/tags", response_model=Profile)
async def update_bullet_tags(
    exp_id: str,
    bullet_id: str,
    tags: list[str],
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await svc_get_profile(db, current_user.id)
    # Find the bullet and update tags
    found = False
    for exp in profile.experiences:
        if exp.id == exp_id:
            for bullet in exp.bullets:
                if bullet.id == bullet_id:
                    bullet.tags = tags
                    found = True
                    break
        if found: break
    
    if not found:
        raise HTTPException(status_code=404, detail="Bullet not found")
        
    return await svc_update_profile(db, current_user.id, profile)

@router.patch("/reorder", response_model=Profile)
async def reorder_items(
    section: str, # "experiences", "projects", "bullets"
    parent_id: str, # exp_id or proj_id if section is bullets
    ordered_ids: list[str],
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await svc_get_profile(db, current_user.id)
    
    if section == "experiences":
        profile.experiences.sort(key=lambda x: ordered_ids.index(x.id) if x.id in ordered_ids else 999)
    elif section == "projects":
        profile.projects.sort(key=lambda x: ordered_ids.index(x.id) if x.id in ordered_ids else 999)
    elif section == "bullets":
        # Find the parent experience or project
        for exp in profile.experiences:
            if exp.id == parent_id:
                exp.bullets.sort(key=lambda x: ordered_ids.index(x.id) if x.id in ordered_ids else 999)
                break
        for proj in profile.projects:
            if proj.id == parent_id:
                proj.bullets.sort(key=lambda x: ordered_ids.index(x.id) if x.id in ordered_ids else 999)
                break
    else:
        raise HTTPException(status_code=400, detail="Invalid section")
        
    return await svc_update_profile(db, current_user.id, profile)
