from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.routers.resumes import _get_user_resume
from app.services.auth_service import get_current_user
from app.services.latex_service import render_template, compile_pdf

router = APIRouter(prefix="/api/v1/resumes", tags=["pdf"])


@router.post("/{resume_id}/pdf")
async def generate_pdf(
    resume_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    resume = await _get_user_resume(resume_id, user, db)

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

    # Pass template_config for custom template
    if resume.template_key == "custom" and resume.template_config:
        data["config"] = resume.template_config
    elif resume.template_key == "custom":
        data["config"] = {
            "font_size": 11, "margin": 0.5, "accent_color": None,
            "header_centered": True, "section_style": "rule",
            "section_case": "smallcaps", "compact": False,
        }

    try:
        tex_content = render_template(resume.template_key, data)
        pdf_bytes = await compile_pdf(tex_content)
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail=f"Template '{resume.template_key}' not found")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{resume.title}.pdf"'},
    )
