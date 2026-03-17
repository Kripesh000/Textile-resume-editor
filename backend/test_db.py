import asyncio
from app.database import async_session
from app.db_models import Resume, Section
from app.services.latex_service import render_template
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def main():
    async with async_session() as db:
        resumes = (await db.execute(select(Resume).options(
            selectinload(Resume.sections)
        ))).scalars().all()
        for resume in resumes:
            print(f"Resume: {resume.id} / Template: {resume.template_key}")
            try:
                data = {
                    "header": resume.header_data or {},
                    "sections": [
                        {
                            "type": s.section_type,
                            "title": s.title,
                            "entries": s.items or [],
                        }
                        for s in resume.sections
                    ],
                }
                
                # Add config for custom templates
                if resume.template_key == "custom" and resume.template_config:
                    data["config"] = resume.template_config
                elif resume.template_key == "custom":
                    data["config"] = {
                        "font_size": 11, "margin": 0.5, "accent_color": None,
                        "header_centered": True, "section_style": "rule",
                        "section_case": "smallcaps", "compact": False,
                    }
                    
            except Exception as e:
                print(e)
                continue
            
            try:
                tex = render_template(resume.template_key, data)
                with open(f"test_out_{resume.id}.tex", "w") as f:
                    f.write(tex)
                print(f"Wrote test_out_{resume.id}.tex")
            except Exception as e:
                print(f"Error rendering {resume.id}: {e}")

asyncio.run(main())
