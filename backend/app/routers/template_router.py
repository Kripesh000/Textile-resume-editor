from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import fitz # PyMuPDF
from io import BytesIO

from app.models import TemplateConfig
from app.services.template_service import list_templates, get_template
from app.services.latex_service import render_template, compile_pdf

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])

@router.get("", response_model=list[TemplateConfig])
async def get_all_templates():
    """List all available LaTeX templates and their configurations."""
    return list_templates()

@router.get("/{template_id}", response_model=TemplateConfig)
async def get_single_template(template_id: str):
    """Get the configuration for a specific template."""
    return get_template(template_id)

@router.get("/{template_id}/thumbnail")
async def get_template_thumbnail(template_id: str):
    """Generates a PNG thumbnail for the requested template.
    
    Renders with dummy user data to show what the template looks like.
    """
    # Verify it exists
    get_template(template_id)
    
    dummy_data = {
        "header_data": {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "555-123-4567",
            "linkedin": "linkedin.com/in/jane",
            "github": "github.com/jane"
        },
        "sections": [
            {
                "title": "Experience",
                "type": "experience",
                "entries": [
                    {
                        "company": "Tech Corp",
                        "location": "San Francisco, CA",
                        "role": "Senior Software Engineer",
                        "start": "Jan 2020",
                        "end": "Present",
                        "bullets": [
                            {"text": "Architected and delivered scalable microservices reaching 1M+ active users."},
                            {"text": "Reduced infrastructure costs by 30% via Kubernetes optimization."}
                        ]
                    }
                ]
            },
            {
                "title": "Education",
                "type": "education",
                "entries": [
                    {
                        "institution": "University of Computer Science",
                        "location": "Boston, MA",
                        "degree": "B.S. in Computer Science",
                        "end": "May 2019",
                        "gpa": "3.8/4.0",
                        "coursework": "Data Structures, Algorithms",
                    }
                ]
            }
        ]
    }
    
    try:
        tex_content = render_template(template_id, dummy_data)
        pdf_bytes = await compile_pdf(tex_content)
        
        # Convert first page of PDF to PNG
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=150) # 150 DPI is a good size for thumbnails
        png_bytes = pix.tobytes("png")
        
        return Response(content=png_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate template thumbnail: {str(e)}")
