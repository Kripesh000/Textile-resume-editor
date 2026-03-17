"""Stateless PDF resume parser using normalization and confidence scoring."""

import re
from typing import Any, Optional
from app.services.normalizer_service import normalize_pdf
from app.services.scoring_service import get_scoring_engine
from app.services.ai_parser_service import resolve_ambiguous_headings, parse_section_content, verify_and_repair
from app.schemas.parser_schema import ResumeParseResult, ParsedSection, ParsedHeader
from app.services.parsing_rules import split_mixed_section

# Reuse regex patterns from old service
EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")
PHONE_RE = re.compile(r"[\(]?\d{3}[\)]?[\s\-.]?\d{3}[\s\-.]?\d{4}")
URL_RE = re.compile(r"(?:https?://)?(?:www\.)?[\w.-]+\.\w{2,}(?:/[\w./-]*)?")
DATE_RANGE_RE = re.compile(
    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|"
    r"\d{1,2}/\d{4}|\d{4})"
    r"\s*[-–—]\s*"
    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|"
    r"\d{1,2}/\d{4}|\d{4}|[Pp]resent|[Cc]urrent)",
    re.IGNORECASE,
)
BULLET_RE = re.compile(r"^\s*[•\-\*\u2022\u25CF\u25CB\u2023]\s*")

async def parse_pdf(file_bytes: bytes) -> dict:
    """Entry point for stateless PDF parsing."""
    # 1. Normalize
    doc = normalize_pdf(file_bytes)
    
    # 2. Score lines
    engine = get_scoring_engine()
    scored_lines = engine.score_document(doc)
    
    # 3. Extract Header
    header, current_idx = _extract_header(scored_lines)
    
    # 4. Group into sections using high-confidence headings
    raw_sections = _group_sections(scored_lines[current_idx:])
    
    # 5. Resolve ambiguity with AI (Ambiguity = score between 0.4 and 0.7)
    ambiguous = [s for s in raw_sections if 0.4 <= s["max_score"] < 0.7]
    if ambiguous:
        titles = [s["title"] for s in ambiguous]
        classifications = await resolve_ambiguous_headings(titles)
        for s in ambiguous:
            if s["title"] in classifications:
                s["section_type"] = classifications[s["title"]]
                s["max_score"] = 0.8  # Upgraded by AI
    
    # 6. Parse section content into structured items
    parsed_sections = []
    for rs in raw_sections:
        section_type = rs["section_type"] if rs["max_score"] >= 0.4 else "generic"
        parsed_sec = await _parse_section_items(section_type, rs["title"], rs["lines"])
        parsed_sections.append(parsed_sec)

    # Flatten nested mixed sections if any
    final_sections = []
    for sec in parsed_sections:
        # split_mixed_section returns list of section dicts
        for split_sec in split_mixed_section(sec["title"], sec["items"]):
            final_sections.append(split_sec)

    return {
        "header": header,
        "sections": final_sections,
        # In a real implementation we'd also detect style here
        "template_config": _default_config() 
    }

def _extract_header(scored_lines: list[dict]) -> tuple[dict, int]:
    """
    Extract contact info from the beginning lines.
    Returns (header_data, lines_consumed_index).
    """
    header = {"name": "", "email": "", "phone": "", "linkedin": "", "github": "", "website": ""}
    
    # Concatenate initial lines to search for header info
    # We assume header info is in the first few lines before the first high-confidence section
    all_text = ""
    lines_consumed_index = 0
    for i, line_data in enumerate(scored_lines):
        if line_data["max_score"] >= 0.7: # Found a high-confidence section heading
            lines_consumed_index = i
            break
        all_text += line_data["text"] + "\n"
    
    # If no high-confidence section found, consider all lines as potential header or generic content
    if lines_consumed_index == 0 and scored_lines:
        lines_consumed_index = len(scored_lines)
    
    # Try to extract contact info
    if not header["email"]:
        match = EMAIL_RE.search(all_text)
        if match: header["email"] = match.group(0)
    if not header["phone"]:
        match = PHONE_RE.search(all_text)
        if match: header["phone"] = match.group(0)
    
    for url_match in URL_RE.finditer(all_text):
        url = url_match.group()
        url_l = url.lower()
        if "linkedin" in url_l: header["linkedin"] = url
        elif "github" in url_l: header["github"] = url
        elif "@" not in url: header["website"] = url
        
    # Find first high-confidence section heading to mark end of header
    return header, lines_consumed_index

def _group_sections(scored_lines: list[dict]) -> list[dict]:
    """Group lines into sections based on heading scores."""
    sections = []
    current_section = None
    
    for line_data in scored_lines:
        # High confidence heading (> 0.7)
        if line_data["max_score"] >= 0.7:
            if current_section:
                sections.append(current_section)
            current_section = {
                "title": line_data["text"],
                "section_type": line_data["primary_type"],
                "max_score": line_data["max_score"],
                "lines": []
            }
        elif current_section:
            current_section["lines"].append(line_data["text"])
        else:
            # Leading text before first section
            current_section = {
                "title": "Introduction",
                "section_type": "generic",
                "max_score": 0.5,
                "lines": [line_data["text"]]
            }
            
    if current_section:
        sections.append(current_section)
    return sections

async def _parse_section_items(section_type: str, title: str, lines: list[str]) -> dict:
    """
    Draft & Verify flow (Principle #2):
    1. Generate a rule-based draft.
    2. Use AI to verify and repair the draft against raw text.
    """
    parsers = {
        "experience": _parse_experience,
        "education": _parse_education,
        "project": _parse_projects,
        "skills": _parse_skills,
    }
    parser = parsers.get(section_type, _parse_generic)
    draft = parser(lines)
    
    # AI Verification layer for structured content
    if section_type in ["experience", "education", "project"] and len(lines) > 0:
        raw_text = "\n".join(lines)
        # AI verifies the draft and repairs any errors
        verified_items = await verify_and_repair(section_type, raw_text, draft)
        if verified_items:
            draft = verified_items

    return {
        "section_type": section_type,
        "title": title,
        "items": draft
    }

def _default_config() -> dict:
    return {
        "font_size": 11,
        "margin": 0.5,
        "accent_color": None,
        "header_centered": True,
        "section_style": "rule",
        "section_case": "smallcaps",
        "compact": False,
    }

# --- Item Parsers (Converted to pure functions) ---

def _parse_experience(lines: list[str]) -> list[dict]:
    items = []
    current: Optional[dict] = None
    for line in lines:
        date_match = DATE_RANGE_RE.search(line)
        is_bullet = BULLET_RE.match(line)
        if date_match and not is_bullet:
            if current: items.append(current)
            current = {"company": "", "role": "", "location": "", "start_date": date_match.group(1), "end_date": date_match.group(2), "bullets": []}
            before = line[:date_match.start()].strip().rstrip("|,–—-").strip()
            if before: current["role"] = before
        elif is_bullet:
            if not current: current = {"company": "", "role": "Experience", "location": "", "start_date": "", "end_date": "", "bullets": []}
            current["bullets"].append(BULLET_RE.sub("", line).strip())
        elif line.strip():
            if not current: current = {"company": "", "role": line.strip(), "location": "", "start_date": "", "end_date": "", "bullets": []}
            elif not current["company"]: current["company"] = line.strip()
    if current: items.append(current)
    return items

def _parse_education(lines: list[str]) -> list[dict]:
    items = []
    current: Optional[dict] = None
    for line in lines:
        date_match = DATE_RANGE_RE.search(line)
        if date_match:
            if current: items.append(current)
            current = {"institution": "", "degree": "", "location": "", "start_date": date_match.group(1), "end_date": date_match.group(2), "details": []}
            before = line[:date_match.start()].strip().rstrip("|,–—-").strip()
            if before: current["institution"] = before
        elif line.strip():
            if not current: current = {"institution": line.strip(), "degree": "", "location": "", "start_date": "", "end_date": "", "details": []}
            else: current["details"].append(line.strip())
    if current: items.append(current)
    return items

def _parse_projects(lines: list[str]) -> list[dict]:
    items = []
    current: Optional[dict] = None
    for line in lines:
        is_bullet = BULLET_RE.match(line)
        if is_bullet:
            if not current: current = {"name": "Project", "tech_stack": "", "url": "", "bullets": []}
            current["bullets"].append(BULLET_RE.sub("", line).strip())
        elif line.strip():
            if current: items.append(current)
            current = {"name": line.strip(), "tech_stack": "", "url": "", "bullets": []}
    if current: items.append(current)
    return items

def _parse_skills(lines: list[str]) -> list[dict]:
    items = []
    for line in lines:
        stripped = BULLET_RE.sub("", line).strip()
        if not stripped: continue
        colon_match = re.match(r"^([^:]+):\s*(.+)$", stripped)
        if colon_match:
            items.append({"category": colon_match.group(1).strip(), "items": [s.strip() for s in colon_match.group(2).split(",") if s.strip()]})
        else:
            items.append({"category": "Skills", "items": [s.strip() for s in stripped.split(",") if s.strip()]})
    return items

def _parse_generic(lines: list[str]) -> list[dict]:
    return [{"text": BULLET_RE.sub("", l).strip()} for l in lines if l.strip()]
