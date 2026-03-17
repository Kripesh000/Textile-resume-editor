import asyncio
from sqlalchemy import select
from app.database import async_session
from app.db_models import UserDB, ProfileDB, ResumeVariantDB
from app.main import app
from httpx import AsyncClient, ASGITransport
import uuid

async def test_render():
    async with async_session() as db:
        # Create a new unique user to avoid unique constraint issues
        test_email = f"test_{uuid.uuid4().hex[:8]}@test.com"
        user = UserDB(email=test_email, name="Test User", hashed_password="pwd")
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        profile = ProfileDB(user_id=user.id, data={"user_id": user.id, "name": "Test User", "email": "test@test.com", "phone": "123-456-7890", "experiences": [], "projects": [], "education": [], "skill_categories": [], "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-01T00:00:00Z"})
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        
        variant = ResumeVariantDB(
            user_id=user.id, profile_id=profile.id, template_id="modern_blue", name="My Test Resume",
            data={"id": "v1", "user_id": user.id, "profile_id": profile.id, "name": "My Test Resume", "template_id": "modern_blue", "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-01T00:00:00Z"}
        )
        db.add(variant)
        await db.commit()
        await db.refresh(variant)

        from app.services.auth_service import create_access_token
        token = create_access_token(user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        print(f"Testing render for variant {variant.id}...")
        response = await ac.post(
            f"/api/v1/variants/{variant.id}/render",
            headers={"Authorization": f"Bearer {token}"}
        )
        print("Status Code:", response.status_code)
        if response.status_code == 200:
            print(f"Success! PDF bytes length: {len(response.content)}")
            with open("test_out_render.pdf", "wb") as f:
                f.write(response.content)
        else:
            print("Response:", response.text)

if __name__ == "__main__":
    asyncio.run(test_render())
