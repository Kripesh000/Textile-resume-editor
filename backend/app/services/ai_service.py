import json

import httpx

from app.config import settings

SYSTEM_PROMPT = """You are an expert resume writer. Your task is to improve resume bullet points to be:
1. Action-oriented: Start with a strong action verb
2. Quantifiable: Include metrics and numbers where plausible
3. Concise: Keep each bullet under 120 characters
4. Professional: Use industry-standard resume language
5. Impactful: Focus on achievements and results, not just duties

Return your response as JSON with this exact format:
{"improved_text": "your primary suggestion", "alternatives": ["alternative 1", "alternative 2"]}

Only return the JSON, no other text."""


async def improvise(text: str, context: dict) -> dict:
    context_str = ""
    if context.get("role"):
        context_str += f"Role: {context['role']}. "
    if context.get("company"):
        context_str += f"Company: {context['company']}. "
    if context.get("section_type"):
        context_str += f"Section: {context['section_type']}. "

    prompt = f"{SYSTEM_PROMPT}\n\nContext: {context_str}\nOriginal bullet point: {text}"

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7},
            },
        )
        response.raise_for_status()

    response_text = response.json().get("response", "").strip()

    # Strip markdown code fences if present
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    try:
        result = json.loads(response_text)
        return {
            "improved_text": result.get("improved_text", text),
            "alternatives": result.get("alternatives", []),
        }
    except json.JSONDecodeError:
        return {"improved_text": response_text, "alternatives": []}
