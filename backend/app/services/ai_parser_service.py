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
        f"experience, education, project, skills, or generic.\n"
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
