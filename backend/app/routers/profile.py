from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.profile import ProfileSection, ProfileItem
from app.schemas.profile import (
    ProfileResponse,
    PersonalInfoUpdate,
    PersonalInfoResponse,
    ProfileSectionCreate,
    ProfileSectionUpdate,
    ProfileSectionResponse,
    ProfileItemCreate,
    ProfileItemUpdate,
    ProfileItemResponse,
)
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


# --- Full profile ---

@router.get("", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProfileSection)
        .where(ProfileSection.user_id == current_user.id)
        .options(selectinload(ProfileSection.items))
        .order_by(ProfileSection.order_index)
    )
    sections = result.scalars().all()

    info = current_user.personal_info or {}
    personal = PersonalInfoResponse(
        name=current_user.name,
        email=info.get("email", current_user.email),
        phone=info.get("phone", ""),
        linkedin=info.get("linkedin", ""),
        github=info.get("github", ""),
        website=info.get("website", ""),
    )
    return ProfileResponse(personal_info=personal, sections=sections)


# --- Personal info ---

@router.put("/personal", response_model=PersonalInfoResponse)
async def update_personal_info(
    data: PersonalInfoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    info = dict(current_user.personal_info or {})
    for field in ("phone", "linkedin", "github", "website", "email"):
        val = getattr(data, field, None)
        if val is not None:
            info[field] = val
    if data.name is not None:
        current_user.name = data.name
    current_user.personal_info = info
    await db.commit()
    await db.refresh(current_user)

    return PersonalInfoResponse(
        name=current_user.name,
        email=info.get("email", current_user.email),
        phone=info.get("phone", ""),
        linkedin=info.get("linkedin", ""),
        github=info.get("github", ""),
        website=info.get("website", ""),
    )


# --- Sections ---

@router.post("/sections", response_model=ProfileSectionResponse, status_code=status.HTTP_201_CREATED)
async def create_section(
    data: ProfileSectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    section = ProfileSection(
        user_id=current_user.id,
        section_type=data.section_type,
        title=data.title,
        order_index=data.order_index,
    )
    db.add(section)
    await db.commit()
    # Re-fetch with items loaded
    result = await db.execute(
        select(ProfileSection)
        .where(ProfileSection.id == section.id)
        .options(selectinload(ProfileSection.items))
    )
    return result.scalar_one()


@router.put("/sections/{section_id}", response_model=ProfileSectionResponse)
async def update_section(
    section_id: str,
    data: ProfileSectionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProfileSection)
        .where(ProfileSection.id == section_id, ProfileSection.user_id == current_user.id)
        .options(selectinload(ProfileSection.items))
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    if data.title is not None:
        section.title = data.title
    if data.order_index is not None:
        section.order_index = data.order_index
    await db.commit()
    await db.refresh(section)
    return section


@router.delete("/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_section(
    section_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProfileSection).where(ProfileSection.id == section_id, ProfileSection.user_id == current_user.id)
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    await db.delete(section)
    await db.commit()


# --- Items ---

@router.post("/sections/{section_id}/items", response_model=ProfileItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    section_id: str,
    data: ProfileItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProfileSection).where(ProfileSection.id == section_id, ProfileSection.user_id == current_user.id)
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    item = ProfileItem(section_id=section_id, data=data.data, order_index=data.order_index)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.put("/items/{item_id}", response_model=ProfileItemResponse)
async def update_item(
    item_id: str,
    data: ProfileItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProfileItem)
        .join(ProfileSection)
        .where(ProfileItem.id == item_id, ProfileSection.user_id == current_user.id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if data.data is not None:
        item.data = data.data
    if data.order_index is not None:
        item.order_index = data.order_index
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProfileItem)
        .join(ProfileSection)
        .where(ProfileItem.id == item_id, ProfileSection.user_id == current_user.id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.delete(item)
    await db.commit()


# --- Import profile items into a resume ---

@router.post("/import-to-resume")
async def import_to_resume(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Import selected profile items into a resume section.
    Body: { resume_id, section_id, item_ids: [...] }
    Appends the profile items' data to the resume section's items list.
    """
    from app.models.resume import Resume, Section

    resume_id = data.get("resume_id")
    section_id = data.get("section_id")
    item_ids = data.get("item_ids", [])

    if not resume_id or not item_ids:
        raise HTTPException(status_code=400, detail="resume_id and item_ids required")

    # Verify resume ownership
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == current_user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Get profile items
    result = await db.execute(
        select(ProfileItem)
        .join(ProfileSection)
        .where(ProfileItem.id.in_(item_ids), ProfileSection.user_id == current_user.id)
    )
    profile_items = result.scalars().all()

    if section_id:
        # Append to existing section
        result = await db.execute(
            select(Section).where(Section.id == section_id, Section.resume_id == resume_id)
        )
        section = result.scalar_one_or_none()
        if not section:
            raise HTTPException(status_code=404, detail="Section not found")
        current_items = list(section.items or [])
        for pi in profile_items:
            current_items.append(pi.data)
        section.items = current_items
    else:
        # Caller didn't specify a section — error
        raise HTTPException(status_code=400, detail="section_id required")

    await db.commit()
    return {"status": "ok", "imported": len(profile_items)}


# --- Save resume section to profile ---

@router.post("/save-from-resume")
async def save_from_resume(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save a resume section's items to the user's profile.
    Body: { resume_id, section_id }
    Creates or finds a matching profile section and adds items (skipping duplicates).
    """
    from app.models.resume import Resume, Section
    import json

    resume_id = data.get("resume_id")
    section_id = data.get("section_id")

    if not resume_id or not section_id:
        raise HTTPException(status_code=400, detail="resume_id and section_id required")

    # Verify resume ownership and get the section
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == current_user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    result = await db.execute(
        select(Section).where(Section.id == section_id, Section.resume_id == resume_id)
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    # Find or create a profile section of the same type
    result = await db.execute(
        select(ProfileSection)
        .where(ProfileSection.user_id == current_user.id, ProfileSection.section_type == section.section_type)
        .options(selectinload(ProfileSection.items))
    )
    profile_section = result.scalar_one_or_none()

    if not profile_section:
        # Count existing profile sections for order_index
        count_result = await db.execute(
            select(ProfileSection).where(ProfileSection.user_id == current_user.id)
        )
        order = len(count_result.scalars().all())
        profile_section = ProfileSection(
            user_id=current_user.id,
            section_type=section.section_type,
            title=section.title,
            order_index=order,
        )
        db.add(profile_section)
        await db.flush()
        profile_section_items = []
    else:
        profile_section_items = profile_section.items or []

    # Get existing profile item data as JSON strings for dedup
    existing_data = {json.dumps(pi.data, sort_keys=True) for pi in profile_section_items}

    added = 0
    for item_data in (section.items or []):
        key = json.dumps(item_data, sort_keys=True)
        if key not in existing_data:
            pi = ProfileItem(
                section_id=profile_section.id,
                data=item_data,
                order_index=len(profile_section_items) + added,
            )
            db.add(pi)
            existing_data.add(key)
            added += 1

    await db.commit()
    return {"status": "ok", "added": added, "section_type": section.section_type}
