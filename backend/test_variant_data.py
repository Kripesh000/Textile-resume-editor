import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.db_models import ResumeVariantDB

from app.config import settings

async def main():
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(ResumeVariantDB))
        variants = result.scalars().all()
        for v in variants:
            print("Variant ID:", v.id)
            for s in (v.data.get("sections") or []):
                print("  Section:", s.get("title"))
                for i, item in enumerate(s.get("items", [])):
                    print(f"    Item {i}: {item.get('role', item.get('institution', item.get('name', '???')))}")

if __name__ == "__main__":
    asyncio.run(main())
