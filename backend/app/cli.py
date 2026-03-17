import asyncio
import argparse
import os
import json
import fitz  # PyMuPDF
from pathlib import Path
from app.services.template_service import list_templates
from app.services.latex_service import render_template, compile_pdf

DUMMY_DATA = {
    "header_data": {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "555-123-4567",
        "linkedin": "linkedin.com/in/jane",
        "github": "github.com/jane",
        "website": "janedoe.com"
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
        },
        {
            "title": "Skills",
            "type": "skills",
            "entries": [
                {
                    "name": "Languages",
                    "items": ["Python", "JavaScript", "Go", "LaTeX"]
                }
            ]
        }
    ]
}

async def generate_thumbnails():
    templates = list_templates()
    templates_dir = Path(__file__).parent / "templates"
    
    for template in templates:
        print(f"Generating thumbnail for {template.id}...")
        try:
            tex_content = render_template(template.id, DUMMY_DATA)
            pdf_bytes = await compile_pdf(tex_content)
            
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page = doc.load_page(0)
            pix = page.get_pixmap(dpi=150)
            
            output_path = templates_dir / template.id / "thumbnail.png"
            pix.save(str(output_path))
            print(f"  Success: {output_path}")
        except Exception as e:
            print(f"  Error generating thumbnail for {template.id}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["generate-thumbnails"])
    args = parser.parse_args()
    
    if args.command == "generate-thumbnails":
        asyncio.run(generate_thumbnails())
