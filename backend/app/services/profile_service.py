from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.db_models import ProfileDB, UserDB
from app.models import Profile

async def get_profile(db: AsyncSession, user_id: str) -> Profile:
    result = await db.execute(select(ProfileDB).where(ProfileDB.user_id == user_id))
    profile_db = result.scalar_one_or_none()
    
    if not profile_db:
        # Create an empty profile for this user if it doesn't exist
        user_result = await db.execute(select(UserDB).where(UserDB.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        empty_profile = Profile(
            user_id=user_id,
            name=user.name,
            email=user.email,
            phone="",
        )
        profile_db = ProfileDB(
            user_id=user_id,
            data=empty_profile.model_dump()
        )
        db.add(profile_db)
        await db.commit()
        await db.refresh(profile_db)
        
    return Profile(**profile_db.data)

async def update_profile(db: AsyncSession, user_id: str, profile_data: Profile) -> Profile:
    result = await db.execute(select(ProfileDB).where(ProfileDB.user_id == user_id))
    profile_db = result.scalar_one_or_none()
    
    if not profile_db:
        profile_db = ProfileDB(
            user_id=user_id,
            data=profile_data.model_dump()
        )
        db.add(profile_db)
    else:
        profile_db.data = profile_data.model_dump()
        
    await db.commit()
    await db.refresh(profile_db)
    return Profile(**profile_db.data)
