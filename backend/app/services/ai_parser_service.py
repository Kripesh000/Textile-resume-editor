"""Lightweight AI heading classifier using a local Ollama model.

Only used to classify section headings that the rule-based parser couldn't
match. Sends a tiny prompt (just the heading titles) for fast response.
"""

import json

import httpx

from app.config import settings


async def classify_headings(titles: list[str]) -> dict[str, str]:
    """Classify unknown section headings into resume section types.

    Args:
        titles: List of section heading strings to classify.

    Returns:
        Dict mapping each title to one of: experience, education, project, skills, generic.
    """
    if not titles:
        return {}

    titles_str = "\n".join(f"- {t}" for t in titles)
    prompt = (
        f"Classify each resume section heading into exactly one type: "
        f"experience, education, project, skills, or generic.\n\n"
        f"Classification rules:\n"
        f"- experience: jobs, internships, work history, leadership, volunteer, activities, extracurriculars\n"
        f"- education: schools, degrees, coursework, academic background\n"
        f"- project: projects, hackathons, research, publications, open source contributions\n"
        f"- skills: technical skills, tools, technologies, programming languages, competencies\n"
        f"- generic: awards, honors, certifications, interests, or anything that doesn't fit above\n\n"
        f"Return ONLY a JSON object mapping each heading to its type.\n\n"
        f"Headings:\n{titles_str}\n\nJSON:"
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.0, "num_predict": 256},
                },
            )
            response.raise_for_status()

        text = response.json().get("response", "").strip()

        # Strip markdown fences
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])

        result = json.loads(text)
        if isinstance(result, dict):
            # Validate values
            valid_types = {"experience", "education", "project", "skills", "generic"}
            return {k: v for k, v in result.items() if v in valid_types}

    except Exception:
        pass

    return {}

# Alias for semantic clarity in the new scoring-based flow
resolve_ambiguous_headings = classify_headings



async def parse_section_content(section_type: str, raw_text: str) -> list[dict]:
    """Full extraction from raw text."""
    if not raw_text.strip():
        return []

    prompts = {
        "experience": (
            "Extract work experience items from this text. Each item should have: "
            "company, role, location, start, end, and bullets (list of strings)."
        ),
        "education": (
            "Extract education items from this text. Each item should have: "
            "institution, degree, location, end, gpa (optional), coursework (optional)."
        ),
        "project": (
            "Extract project items from this text. Each item should have: "
            "name, tech_stack, date, and bullets (list of strings)."
        ),
        "skills": (
            "Extract skill categories from this text. Each item should have: "
            "name (category title) and items (list of skill strings)."
        ),
    }

    prompt_base = prompts.get(section_type, "Extract structured items from this text.")
    prompt = (
        f"{prompt_base}\n\n"
        f"Rules:\n"
        f"- Return ONLY valid JSON list of objects.\n"
        f"- Use empty strings for missing fields.\n\n"
        f"Text:\n{raw_text}\n\nJSON:"
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.0},
                },
            )
            response.raise_for_status()

        text = response.json().get("response", "").strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        
        result = json.loads(text.strip())
        if not isinstance(result, list):
            return []
            
        return _normalize_items(result, section_type)
    except Exception:
        return []


def _normalize_items(items: list[dict], section_type: str) -> list[dict]:
    """Shared helper to normalize keys for consistency across all AI outputs."""
    normalized = []
    for item in items:
        n_item = {}
        for k, v in item.items():
            key = k.lower().replace(" ", "_").strip()
            # Map common variations to schema names
            if key in ["bullets", "bullet_points", "point", "description", "details", "highlights", "responsibilities", "bulletpoints"]:
                key = "bullets"
            elif key in ["start_date", "from", "started", "start"]:
                key = "start"
            elif key in ["end_date", "to", "ended", "end", "until"]:
                key = "end"
            elif key in ["university", "school", "college", "institute", "academy"]:
                key = "institution"
            elif key in ["role", "job_title", "position", "title"] and section_type == "experience":
                key = "role"
            elif key in ["name", "project_name", "title"] and section_type == "project":
                key = "name"
            n_item[key] = v
        normalized.append(n_item)
    return normalized


async def parse_section_content(section_type: str, raw_text: str) -> list[dict]:
    """Full extraction from raw text."""
    if not raw_text.strip():
        return []

    prompts = {
        "experience": (
            "Extract work experience items from this text. Each item MUST have: "
            "company, role, location, start, end, and bullets (list of strings)."
        ),
        "education": (
            "Extract education items from this text. Each item MUST have: "
            "institution, degree, location, end, gpa (optional), coursework (optional)."
        ),
        "project": (
            "Extract project items from this text. Each item MUST have: "
            "name, tech_stack, date, and bullets (list of strings)."
        ),
        "skills": (
            "Extract skill categories from this text. Each item MUST have: "
            "name (category title) and items (list of skill strings)."
        ),
    }

    prompt_base = prompts.get(section_type, "Extract structured items from this text.")
    prompt = (
        f"{prompt_base}\n\n"
        f"Rules:\n"
        f"- Return ONLY valid JSON list of objects.\n"
        f"- Use empty strings for missing fields.\n"
        f"- Fix any obvious typos in the source text.\n\n"
        f"Text:\n{raw_text}\n\nJSON:"
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.0},
                },
            )
            response.raise_for_status()

        text = response.json().get("response", "").strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        
        result = json.loads(text.strip())
        if not isinstance(result, list):
            return []
            
        return _normalize_items(result, section_type)
    except Exception:
        return []


async def verify_and_repair(section_type: str, raw_text: str, draft: list[dict]) -> list[dict]:
    """
    Efficiently verify and repair a rule-based draft against raw text.
    Fulfills Principle #2: AI as a verification system.
    """
    if not raw_text.strip():
        return draft
    
    draft_json = json.dumps(draft, sort_keys=True)
    prompt = (
        f"You are an expert resume editor. Your job is to REPAIR the DRAFT below using the RAW TEXT as the absolute source of truth.\n\n"
        f"RAW TEXT:\n{raw_text}\n\n"
        f"DRAFT (Likely contains errors, typos, or missing fields):\n{draft_json}\n\n"
        f"CRITICAL RULES:\n"
        f"1. DEDUPLICATE: Do NOT return the same item twice. If the draft has an item and the raw text has the same item, return it once (repaired).\n"
        f"2. MERGE: If the draft has a partial item (e.g. missing bullets) and raw text has those bullets, MERGE them into ONE item.\n"
        f"3. FIX TYPOS: If the draft says 'Gogle' but raw text says 'Google', you MUST change it to 'Google'.\n"
        f"4. FILL MISSING: If the draft has empty strings but raw text has info, you MUST fill them.\n"
        f"5. SCHEMA: Return ONLY a JSON list of objects with these keys: company, role, location, start, end, bullets.\n\n"
        f"Corrected JSON:"
    )

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.0},
                },
            )
            response.raise_for_status()

        text = response.json().get("response", "").strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        
        result = json.loads(text.strip())
        if not isinstance(result, list):
            return draft 
            
        return _normalize_items(result, section_type)
    except Exception:
        return draft
