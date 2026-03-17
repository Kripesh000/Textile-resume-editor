import json
import httpx
from pydantic import ValidationError

from app.config import settings
from app.models import Profile

SYSTEM_PROMPT = """You are an expert data extraction AI. Follow these instructions strictly:
1. Extract the resume information from the text provided into a structured JSON document.
2. The output MUST exactly match the JSON schema for the Profile object.
3. Every UUID field (id) MUST be generated as a valid hexadecimal string without hyphens.
4. Dates should be returned as strings in "MMM YYYY" format exactly.
5. If a piece of information is missing, use an empty string "" for strings, and an empty list [] for lists. Do NOT omit fields.
6. The outermost object must have keys: "user_id", "name", "email", "phone", "linkedin", "github", "website", "experiences", "projects", "education", "skill_categories".
7. DO NOT wrapping your output in markdown code blocks. Give ONLY the raw JSON output.
"""

async def parse_resume_to_profile(text_content: str, user_id: str) -> Profile:
    """Uses a local Ollama model to extract raw resume text into the exact Profile schema."""
    
    # We pass the schema explicitly to ensure the LLM knows the expected shape.
    schema_instructions = f"""
    The output must strictly conform to this JSON structure:
    {{
        "user_id": "{user_id}",
        "name": "string",
        "email": "string",
        "phone": "string",
        "linkedin": "string | null",
        "github": "string | null",
        "website": "string | null",
        "experiences": [
            {{
                "id": "uuid hex string",
                "company": "string",
                "role": "string",
                "location": "string",
                "start": "string",
                "end": "string",
                "tags": ["string"],
                "bullets": [
                    {{
                        "id": "uuid hex string",
                        "text": "string",
                        "tags": ["string"],
                        "order": 0
                    }}
                ]
            }}
        ],
        "projects": [
            {{
                "id": "uuid hex string",
                "name": "string",
                "tech_stack": "string",
                "date": "string",
                "tags": ["string"],
                "bullets": [
                    {{
                        "id": "uuid hex string",
                        "text": "string",
                        "tags": ["string"],
                        "order": 0
                    }}
                ]
            }}
        ],
        "education": [
            {{
                "id": "uuid hex string",
                "institution": "string",
                "degree": "string",
                "location": "string",
                "end": "string",
                "gpa": "string | null",
                "coursework": "string | null",
                "awards": "string | null"
            }}
        ],
        "skill_categories": [
            {{
                "id": "uuid hex string",
                "name": "string",
                "items": ["string"],
                "tags": ["string"]
            }}
        ]
    }}
    """

    prompt = f"{SYSTEM_PROMPT}\n{schema_instructions}\n\nResume Text:\n{text_content}"

    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,  # Deterministic output
                    "num_predict": 4096  # Needs a large window for full profiles
                },
            },
        )
        response.raise_for_status()

    response_text = response.json().get("response", "").strip()

    # Strip markdown fences if the LLM didn't listen to instructions
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])
        if response_text.startswith("json"):
            response_text = response_text[4:].strip()

    try:
        raw_json = json.loads(response_text)
        # Force user_id to match the authenticated user
        raw_json["user_id"] = user_id
        
        # Validate against the strict Pydantic model
        profile = Profile(**raw_json)
        return profile
    except (json.JSONDecodeError, ValidationError) as e:
        # Re-raise with the actual LLM output to help debugging
        raise ValueError(f"Failed to parse or validate LLM output: {str(e)}\nRaw Response: {response_text}")
