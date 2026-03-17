import re
from typing import Any
from app.services.normalizer_service import normalize_latex
from app.services.parsing_rules import detect_section_type
from app.services.ai_parser_service import parse_section_content

async def parse_latex(tex_content: str) -> dict:
    """
    Parse LaTeX source deterministically.
    Stateless: Returns structured data but does NOT generate/save templates.
    """
    # 1. Normalize (extracts key metadata like \section commands)
    doc = normalize_latex(tex_content)
    
    # 2. Extract Data
    structured_data = await _extract_data(tex_content)
    
    return {
        "header": structured_data.get("header", {}),
        "sections": structured_data.get("sections", []),
        "raw_source": tex_content # Pass back for lazy template gen storage
    }

def generate_jinja_template(tex_content: str, parsed_data: dict) -> str:
    """
    Lazy template generator. 
    Call this only when the resume needs to be rendered for the first time.
    """
    template = tex_content
    header = parsed_data.get("header", {})
    
    # Replace header info safely
    if header.get("name"):
        template = template.replace(header["name"], r"\VAR{header_data.name | escape_latex}")
    if header.get("email"):
        template = template.replace(header["email"], r"\VAR{header_data.email | escape_latex}")
    if header.get("phone"):
        template = template.replace(header["phone"], r"\VAR{header_data.phone | escape_latex}")
    
    return template

async def _extract_data(tex_content: str) -> dict:
    """Internal helper to extract data from LaTeX."""
    header = {"name": "", "email": "", "phone": "", "linkedin": "", "github": "", "website": ""}
    sections = []

    # --- 1. Header (Regex based for speed/legacy compatibility) ---
    name_patterns = [
        r"\\textbf\{\\Huge\s+\\scshape\s+(.+?)\}",
        r"\\textbf\{\\(?:LARGE|Huge|huge)\s+(?:\\scshape\s+)?(.+?)\}",
        r"\{\\(?:LARGE|Huge|huge)\\bfseries\s+(.+?)\}",
        r"\\name\{(.+?)\}",
    ]
    for pattern in name_patterns:
        match = re.search(pattern, tex_content)
        if match:
            header["name"] = _strip_latex(match.group(1))
            break

    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", tex_content)
    if email_match: header["email"] = email_match.group()

    phone_match = re.search(r"[\(]?\d{3}[\)]?[\s\-.]?\d{3}[\s\-.]?\d{4}", tex_content)
    if phone_match: header["phone"] = phone_match.group()

    # --- 2. Sections ---
    section_matches = list(re.finditer(r"\\section\{(.+?)\}", tex_content))
    for i, sec_match in enumerate(section_matches):
        title = sec_match.group(1).strip()
        start = sec_match.end()
        end = section_matches[i + 1].start() if i + 1 < len(section_matches) else len(tex_content)
        content = tex_content[start:end]
        
        section_type = detect_section_type(title) or "generic"
        
        # Mandatory AI for structured content sections (Principle #2)
        if section_type in ["experience", "education", "project"]:
            items = await parse_section_content(section_type, content)
        else:
            # Fallback to deterministic regex for skills and generic sections
            items = _extract_section_items(content)

        if items:
            sections.append({
                "section_type": section_type,
                "title": title,
                "items": items,
            })

    return {"header": header, "sections": sections}

def _extract_section_items(content: str) -> list[dict]:
    items = []
    # Try to find common environments first
    for cmd_match in re.finditer(r"\\resumeSubheading", content):
        args = _extract_latex_args(content[cmd_match.end():], 4)
        if len(args) == 4:
            items.append({
                "type": "subheading",
                "company": _strip_latex(args[0]),
                "location": _strip_latex(args[1]),
                "role": _strip_latex(args[2]),
                "date": _strip_latex(args[3]),
                "bullets": _extract_bullets(content[cmd_match.end():]),
            })

    if not items:
        # Fallback to items
        for item_match in re.finditer(r"\\item\s+(.+?)(?=\\item|\\end\{itemize\}|$)", content, re.DOTALL):
            cleaned = _strip_latex(item_match.group(1))
            if cleaned:
                items.append({"type": "text", "text": cleaned})
    return items

def _extract_latex_args(text: str, num_args: int) -> list[str]:
    args = []
    i = 0
    for _ in range(num_args):
        while i < len(text) and text[i] in ' \t\n': i += 1
        if i >= len(text) or text[i] != '{': break
        depth = 0; start = i + 1
        while i < len(text):
            if text[i] == '{': depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    args.append(text[start:i].strip())
                    i += 1
                    break
            i += 1
    return args

def _strip_latex(text: str) -> str:
    text = re.sub(r'\\(?:textbf|textit|emph|underline|small|large|huge|scshape|bfseries)\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    text = re.sub(r'[{}]', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def _extract_bullets(content: str) -> list[str]:
    bullets = []
    cutoff = re.search(r"\\resume(?:Subheading|ProjectHeading)", content)
    scope = content[:cutoff.start()] if cutoff else content
    for m in re.finditer(r"\\resumeItem\{(.+?)\}", scope, re.DOTALL):
        bullets.append(_strip_latex(m.group(1)))
    return bullets
