from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.db_models.resume import Resume, Section
from app.db_models.user import User
from app.schemas.resume import (
    ResumeCreate, ResumeUpdate, ResumeResponse, ResumeListItem,
    SectionCreate, SectionUpdate, SectionResponse, SectionReorderItem,
)
from app.services.auth_service import get_current_user
from app.services.pdf_parser_service import parse_pdf
from app.services.latex_parser_service import parse_latex, save_user_template
from app.services.profile_import_service import import_parsed_to_profile

router = APIRouter(prefix="/api/v1/resumes", tags=["resumes"])


async def _get_user_resume(resume_id: str, user: User, db: AsyncSession) -> Resume:
    result = await db.execute(
        select(Resume)
        .options(selectinload(Resume.sections))
        .where(Resume.id == resume_id, Resume.user_id == user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


# --- Resume CRUD ---

@router.post("", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def create_resume(
    data: ResumeCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    resume = Resume(user_id=user.id, title=data.title, template_key=data.template_key)
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return await _get_user_resume(resume.id, user, db)


@router.get("", response_model=list[ResumeListItem])
async def list_resumes(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Resume).where(Resume.user_id == user.id).order_by(Resume.updated_at.desc())
    )
    return result.scalars().all()


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()

    # Validate size (10MB max)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    # Validate PDF magic bytes
    if not content[:5].startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    # Parse PDF
    parsed = await parse_pdf(content)
    header = parsed.get("header", {})
    template_config = parsed.get("template_config", {})

    # Create resume with detected style
    title = header.get("name", "").strip() or "Uploaded Resume"
    resume = Resume(
        user_id=user.id,
        title=title,
        template_key="custom",
        template_config=template_config,
        header_data=header,
    )
    db.add(resume)
    await db.flush()

    # Create sections
    for i, section_data in enumerate(parsed.get("sections", [])):
        section = Section(
            resume_id=resume.id,
            section_type=section_data["section_type"],
            title=section_data["title"],
            order_index=i,
            items=section_data["items"],
        )
        db.add(section)

    await db.commit()

    # Also import parsed data into user's profile
    profile_result = await import_parsed_to_profile(parsed, user.id, db)

    resume_response = await _get_user_resume(resume.id, user, db)
    return resume_response



@router.post("/upload-latex", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_latex(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Validate file type
    filename = file.filename or ""
    if not filename.lower().endswith(".tex"):
        raise HTTPException(status_code=400, detail="Only .tex files are supported")

    content = await file.read()

    # Validate size (5MB max for text files)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")

    try:
        tex_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be valid UTF-8 text")

    # Validate it looks like LaTeX
    if r"\documentclass" not in tex_content:
        raise HTTPException(status_code=400, detail="File does not appear to be a valid LaTeX document")

    # Parse LaTeX using AI
    parsed = await parse_latex(tex_content)
    header = parsed.get("header", {})
    template_content = parsed.get("template")

    # Create resume
    title = header.get("name", "").strip() or "Uploaded Resume"
    resume = Resume(
        user_id=user.id,
        title=title,
        template_key="custom",  # Will be updated if template generation succeeds
        header_data=header,
    )
    db.add(resume)
    await db.flush()

    # Save user-specific template if AI generated one
    if template_content:
        template_key = save_user_template(resume.id, template_content)
        resume.template_key = template_key

    # Create sections
    for i, section_data in enumerate(parsed.get("sections", [])):
        section = Section(
            resume_id=resume.id,
            section_type=section_data.get("section_type", "generic"),
            title=section_data.get("title", "Section"),
            order_index=i,
            items=section_data.get("items", []),
        )
        db.add(section)

    await db.commit()

    # Also import parsed data into user's profile
    profile_result = await import_parsed_to_profile(parsed, user.id, db)

    return await _get_user_resume(resume.id, user, db)


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await _get_user_resume(resume_id, user, db)


@router.put("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: str,
    data: ResumeUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    resume = await _get_user_resume(resume_id, user, db)
    if data.title is not None:
        resume.title = data.title
    if data.template_key is not None:
        resume.template_key = data.template_key
    if data.template_config is not None:
        resume.template_config = data.template_config
    if data.header_data is not None:
        resume.header_data = data.header_data
    await db.commit()
    return await _get_user_resume(resume_id, user, db)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    resume = await _get_user_resume(resume_id, user, db)
    await db.delete(resume)
    await db.commit()


# --- Section CRUD ---

@router.put("/{resume_id}/sections/reorder", response_model=list[SectionResponse])
async def reorder_sections(
    resume_id: str,
    items: list[SectionReorderItem],
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    resume = await _get_user_resume(resume_id, user, db)
    section_map = {s.id: s for s in resume.sections}

    for item in items:
        section = section_map.get(item.section_id)
        if section:
            section.order_index = item.order_index

    await db.commit()
    return (await _get_user_resume(resume_id, user, db)).sections


@router.post("/{resume_id}/sections", response_model=SectionResponse, status_code=status.HTTP_201_CREATED)
async def create_section(
    resume_id: str,
    data: SectionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _get_user_resume(resume_id, user, db)
    section = Section(
        resume_id=resume_id,
        section_type=data.section_type,
        title=data.title,
        order_index=data.order_index,
        items=data.items,
    )
    db.add(section)
    await db.commit()
    await db.refresh(section)
    return section


@router.put("/{resume_id}/sections/{section_id}", response_model=SectionResponse)
async def update_section(
    resume_id: str,
    section_id: str,
    data: SectionUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _get_user_resume(resume_id, user, db)
    result = await db.execute(
        select(Section).where(Section.id == section_id, Section.resume_id == resume_id)
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    if data.title is not None:
        section.title = data.title
    if data.items is not None:
        section.items = data.items
    await db.commit()
    await db.refresh(section)
    return section


@router.delete("/{resume_id}/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_section(
    resume_id: str,
    section_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _get_user_resume(resume_id, user, db)
    result = await db.execute(
        select(Section).where(Section.id == section_id, Section.resume_id == resume_id)
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    await db.delete(section)
    await db.commit()
