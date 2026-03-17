import asyncio
from app.database import async_session
from app.db_models.resume import Resume
from sqlalchemy import select

async def main():
    async with async_session() as db:
        resumes = (await db.execute(select(Resume))).scalars().all()
        for r in resumes:
            print(f"ID: {r.id}, Template Key: {r.template_key}")
            if "74f4154c-11a9-44b5-86b8-698c20fbf1fa" in r.id:
                r.template_key = "custom"
                r.title = "Old Broken AI Resume"
        
        await db.commit()
        print(f"Done.")

asyncio.run(main())
