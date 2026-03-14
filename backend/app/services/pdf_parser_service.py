"""Rule-based PDF resume parser using pdfplumber, with AI heading classification."""

import re
import io
from collections import Counter
import pdfplumber

from app.services.ai_parser_service import classify_headings


# Section heading patterns (case-insensitive)
SECTION_PATTERNS = {
    "experience": re.compile(
        r"^(work\s+experience|professional\s+experience|relevant\s+experience"
        r"|experience|employment(\s+history)?|internship(s)?"
        r"|work\s+history|industry\s+experience|career\s+history)\s*$",
        re.IGNORECASE,
    ),
    "education": re.compile(
        r"^(education|academic(\s+background)?|academic\s+history"
        r"|degrees?|coursework|relevant\s+coursework"
        r"|certifications?(\s+(&|and)\s+education)?)\s*$",
        re.IGNORECASE,
    ),
    "project": re.compile(
        r"^(projects?|personal\s+projects?|academic\s+projects?"
        r"|side\s+projects?|hackathons?|research(\s+projects?)?"
        r"|open\s+source(\s+contributions?)?)\s*$",
        re.IGNORECASE,
    ),
    "skills": re.compile(
        r"^(skills|technical\s+skills|competencies|core\s+competencies"
        r"|technologies|tools(\s+(&|and)\s+technologies)?"
        r"|programming(\s+languages)?|technical\s+proficiencies"
        r"|areas\s+of\s+expertise|expertise)\s*$",
        re.IGNORECASE,
    ),
}

# Regex patterns
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
    """Parse a PDF resume into structured data with AI heading classification."""
    lines = _extract_lines(file_bytes)
    if not lines:
        return {"header": {}, "sections": [], "template_config": _default_config()}

    header, body_start = _extract_header(lines)
    sections = _extract_sections(lines[body_start:])
    template_config = _extract_style(file_bytes)

    # AI step: classify any "generic" section headings
    generic_titles = [s["title"] for s in sections if s["section_type"] == "generic"]
    if generic_titles:
        classifications = await classify_headings(generic_titles)
        for section in sections:
            if section["section_type"] == "generic" and section["title"] in classifications:
                new_type = classifications[section["title"]]
                if new_type != "generic":
                    section["section_type"] = new_type
                    # Convert generic items {text:...} to the expected format
                    section["items"] = _convert_generic_items(new_type, section["items"])

    return {"header": header, "sections": sections, "template_config": template_config}


def _convert_generic_items(section_type: str, items: list[dict]) -> list[dict]:
    """Convert generic {text:...} items to the expected format for a given section type."""
    converted = []
    for item in items:
        text = item.get("text", "")
        if not text:
            converted.append(item)  # Already in proper format
            continue

        if section_type == "experience":
            converted.append({
                "company": "", "role": text, "location": "",
                "start_date": "", "end_date": "", "bullets": [],
            })
        elif section_type == "education":
            converted.append({
                "institution": text, "degree": "", "location": "",
                "start_date": "", "end_date": "", "details": [],
            })
        elif section_type == "project":
            converted.append({
                "name": text, "tech_stack": "", "url": "", "bullets": [],
            })
        elif section_type == "skills":
            converted.append({"category": "Skills", "items": [text]})
        else:
            converted.append(item)
    return converted


def _default_config() -> dict:
    """Return default template configuration."""
    return {
        "font_size": 11,
        "margin": 0.5,
        "accent_color": None,
        "header_centered": True,
        "section_style": "rule",
        "section_case": "smallcaps",
        "compact": False,
    }


def _extract_style(file_bytes: bytes) -> dict:
    """Extract visual style parameters from PDF using character-level data."""
    config = _default_config()

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            if not pdf.pages:
                return config

            page = pdf.pages[0]
            chars = page.chars
            if not chars:
                return config

            page_width = page.width

            # --- Font size detection ---
            sizes = [round(c["size"], 1) for c in chars if c.get("size")]
            if sizes:
                size_counts = Counter(sizes)
                body_size = size_counts.most_common(1)[0][0]
                max_size = max(sizes)

                # Map to closest standard size
                if body_size <= 9.5:
                    config["font_size"] = 10
                    config["compact"] = True
                elif body_size <= 10.5:
                    config["font_size"] = 10
                else:
                    config["font_size"] = 11

            # --- Margin detection ---
            x_positions = [c["x0"] for c in chars if c.get("x0") is not None]
            if x_positions:
                min_x = min(x_positions)
                # Convert points to inches (72 points per inch)
                margin_inches = min_x / 72.0
                if margin_inches >= 0.55:
                    config["margin"] = 0.6
                else:
                    config["margin"] = 0.5

            # --- Color detection ---
            for c in chars:
                color = c.get("non_stroking_color")
                if color and isinstance(color, (list, tuple)):
                    # Check if it's not black/near-black
                    if len(color) == 3:  # RGB
                        r, g, b = color
                        if not (r < 0.1 and g < 0.1 and b < 0.1):
                            # Found a non-black color — use as accent
                            hex_color = "#{:02x}{:02x}{:02x}".format(
                                int(r * 255), int(g * 255), int(b * 255)
                            )
                            config["accent_color"] = hex_color
                            config["section_style"] = "color_rule"
                            break
                    elif len(color) == 1:  # Grayscale
                        pass  # Ignore grayscale

            # --- Header alignment ---
            # Get chars from the first line (largest font = name)
            if sizes:
                name_chars = [c for c in chars if round(c["size"], 1) == max_size]
                if name_chars:
                    name_x0 = min(c["x0"] for c in name_chars)
                    name_x1 = max(c["x1"] for c in name_chars)
                    name_center = (name_x0 + name_x1) / 2
                    page_center = page_width / 2
                    # If name is within 15% of center, it's centered
                    if abs(name_center - page_center) < page_width * 0.15:
                        config["header_centered"] = True
                    else:
                        config["header_centered"] = False

            # --- Section heading style detection ---
            section_heading_lines = _find_section_heading_lines(page)
            if section_heading_lines:
                sample = section_heading_lines[0]
                text = sample.get("text", "")
                if text == text.upper() and not text == text.lower():
                    config["section_case"] = "uppercase"
                else:
                    config["section_case"] = "smallcaps"

            # --- Separator detection (lines/rules) ---
            lines_on_page = page.lines or []
            rects = page.rects or []
            has_separators = len(lines_on_page) > 0 or any(
                r.get("width", 0) > page_width * 0.5 and r.get("height", 0) < 3
                for r in rects
            )
            if not has_separators:
                config["section_style"] = "plain"

    except Exception:
        pass  # Return defaults on any parsing error

    return config


def _find_section_heading_lines(page) -> list[dict]:
    """Find text lines that match section heading patterns."""
    results = []
    text = page.extract_text()
    if not text:
        return results

    for line in text.split("\n"):
        stripped = line.strip()
        if _detect_section_type(stripped):
            results.append({"text": stripped})
    return results


def _extract_lines(file_bytes: bytes) -> list[str]:
    """Extract text lines from PDF."""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        lines = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines.extend(text.split("\n"))
    return [line.strip() for line in lines if line.strip()]


def _extract_header(lines: list[str]) -> tuple[dict, int]:
    """Extract header info from the first few lines before any section heading."""
    header = {"name": "", "email": "", "phone": "", "linkedin": "", "github": "", "website": ""}
    body_start = 0

    # Find where the first section heading starts
    for i, line in enumerate(lines):
        if _detect_section_type(line):
            body_start = i
            break
    else:
        # No sections found — treat first few lines as header, rest as body
        body_start = min(len(lines), 6)

    header_lines = lines[:body_start]

    # Name is typically the first line
    if header_lines:
        header["name"] = header_lines[0]

    # Scan header lines for contact info
    header_text = " ".join(header_lines)

    email_match = EMAIL_RE.search(header_text)
    if email_match:
        header["email"] = email_match.group()

    phone_match = PHONE_RE.search(header_text)
    if phone_match:
        header["phone"] = phone_match.group()

    # Extract URLs and classify them
    for url_match in URL_RE.finditer(header_text):
        url = url_match.group()
        url_lower = url.lower()
        if "linkedin" in url_lower:
            header["linkedin"] = url
        elif "github" in url_lower:
            header["github"] = url
        elif "@" not in url and url_lower not in header.get("email", ""):
            header["website"] = url

    return header, body_start


def _detect_section_type(line: str) -> str | None:
    """Check if a line is a section heading. Returns section type or None."""
    cleaned = line.strip().rstrip(":")
    for section_type, pattern in SECTION_PATTERNS.items():
        if pattern.match(cleaned):
            return section_type
    return None


def _is_section_heading(line: str) -> bool:
    """Check if a line looks like a section heading (short, no bullets, often uppercase or title case)."""
    stripped = line.strip().rstrip(":")
    if not stripped or len(stripped) > 60:
        return False
    if BULLET_RE.match(line):
        return False
    if DATE_RANGE_RE.search(line):
        return False
    # Check if it's a known section type
    if _detect_section_type(stripped):
        return True
    # Heuristic: short line (1-4 words), mostly letters, title case or uppercase
    words = stripped.split()
    if 1 <= len(words) <= 5:
        if stripped == stripped.upper() or stripped == stripped.title():
            # Make sure it's not a name/company (contains no digits typically for headings)
            if not any(c.isdigit() for c in stripped):
                return True
    return False


def _extract_sections(lines: list[str]) -> list[dict]:
    """Split lines into sections based on detected headings (known + generic)."""
    sections = []
    current_type = None
    current_title = None
    current_lines: list[str] = []

    for line in lines:
        known_type = _detect_section_type(line)
        if known_type:
            # Save previous section
            if current_type and current_lines:
                sections.append(_parse_section(current_type, current_title, current_lines))
            current_type = known_type
            current_title = line.strip().rstrip(":")
            current_lines = []
        elif _is_section_heading(line) and (current_type is not None or not current_lines):
            # Unrecognized heading → generic section
            if current_type and current_lines:
                sections.append(_parse_section(current_type, current_title, current_lines))
            current_type = "generic"
            current_title = line.strip().rstrip(":")
            current_lines = []
        else:
            current_lines.append(line)

    # Save last section
    if current_type and current_lines:
        sections.append(_parse_section(current_type, current_title, current_lines))

    return sections


def _parse_section(section_type: str, title: str, lines: list[str]) -> dict:
    """Parse a section's lines into structured items."""
    parsers = {
        "experience": _parse_experience,
        "education": _parse_education,
        "project": _parse_projects,
        "skills": _parse_skills,
        "generic": _parse_generic,
    }
    parser = parsers.get(section_type, _parse_generic)
    return {
        "section_type": section_type,
        "title": title,
        "items": parser(lines),
    }


def _parse_experience(lines: list[str]) -> list[dict]:
    """Parse experience section into structured items."""
    items = []
    current: dict | None = None

    for line in lines:
        date_match = DATE_RANGE_RE.search(line)
        is_bullet = BULLET_RE.match(line)

        if date_match and not is_bullet:
            # This line contains a date range — start a new entry or add dates to current
            if current is None:
                current = {"company": "", "role": "", "location": "", "start_date": "", "end_date": "", "bullets": []}

            current["start_date"] = date_match.group(1)
            current["end_date"] = date_match.group(2)

            # The text before the date is likely role/company info
            before_date = line[:date_match.start()].strip().rstrip("|,–—-").strip()
            if before_date:
                if not current["role"]:
                    current["role"] = before_date
                elif not current["company"]:
                    current["company"] = before_date
        elif is_bullet:
            if current is None:
                current = {"company": "", "role": "", "location": "", "start_date": "", "end_date": "", "bullets": []}
            bullet_text = BULLET_RE.sub("", line).strip()
            if bullet_text:
                current["bullets"].append(bullet_text)
        else:
            # Non-bullet, non-date line — could be role/company header
            stripped = line.strip()
            if not stripped:
                continue

            # If we have an existing entry with bullets, save it and start new
            if current and current["bullets"]:
                items.append(current)
                current = {"company": "", "role": "", "location": "", "start_date": "", "end_date": "", "bullets": []}
                current["role"] = stripped
            elif current is None:
                current = {"company": "", "role": stripped, "location": "", "start_date": "", "end_date": "", "bullets": []}
            elif not current["role"]:
                current["role"] = stripped
            elif not current["company"]:
                current["company"] = stripped
            elif not current["location"]:
                # Try to detect location (contains comma typically)
                current["location"] = stripped

    if current:
        items.append(current)

    return items


def _parse_education(lines: list[str]) -> list[dict]:
    """Parse education section into structured items."""
    items = []
    current: dict | None = None

    for line in lines:
        date_match = DATE_RANGE_RE.search(line)
        is_bullet = BULLET_RE.match(line)

        if date_match and not is_bullet:
            if current is None:
                current = {"institution": "", "degree": "", "location": "", "start_date": "", "end_date": "", "details": []}

            current["start_date"] = date_match.group(1)
            current["end_date"] = date_match.group(2)

            before_date = line[:date_match.start()].strip().rstrip("|,–—-").strip()
            if before_date:
                if not current["institution"]:
                    current["institution"] = before_date
                elif not current["degree"]:
                    current["degree"] = before_date
        elif is_bullet:
            if current is None:
                current = {"institution": "", "degree": "", "location": "", "start_date": "", "end_date": "", "details": []}
            detail_text = BULLET_RE.sub("", line).strip()
            if detail_text:
                current["details"].append(detail_text)
        else:
            stripped = line.strip()
            if not stripped:
                continue

            if current and current["details"]:
                items.append(current)
                current = {"institution": stripped, "degree": "", "location": "", "start_date": "", "end_date": "", "details": []}
            elif current is None:
                current = {"institution": stripped, "degree": "", "location": "", "start_date": "", "end_date": "", "details": []}
            elif not current["institution"]:
                current["institution"] = stripped
            elif not current["degree"]:
                current["degree"] = stripped
            elif not current["location"]:
                current["location"] = stripped
            else:
                # Additional info line — treat as detail
                current["details"].append(stripped)

    if current:
        items.append(current)

    return items


def _parse_projects(lines: list[str]) -> list[dict]:
    """Parse projects section into structured items."""
    items = []
    current: dict | None = None

    for line in lines:
        is_bullet = BULLET_RE.match(line)

        if is_bullet:
            if current is None:
                current = {"name": "", "tech_stack": "", "url": "", "bullets": []}
            bullet_text = BULLET_RE.sub("", line).strip()
            if bullet_text:
                current["bullets"].append(bullet_text)
        else:
            stripped = line.strip()
            if not stripped:
                continue

            # Non-bullet line = new project header
            if current and current["bullets"]:
                items.append(current)

            current = {"name": "", "tech_stack": "", "url": "", "bullets": []}

            # Try to split "Project Name | Tech Stack | URL"
            parts = re.split(r"\s*[|–—]\s*", stripped)
            if parts:
                current["name"] = parts[0].strip()
            if len(parts) > 1:
                # Check if any part is a URL
                for part in parts[1:]:
                    if URL_RE.match(part.strip()):
                        current["url"] = part.strip()
                    elif not current["tech_stack"]:
                        current["tech_stack"] = part.strip()

    if current:
        items.append(current)

    return items


def _parse_skills(lines: list[str]) -> list[dict]:
    """Parse skills section into structured items."""
    items = []

    for line in lines:
        stripped = BULLET_RE.sub("", line).strip()
        if not stripped:
            continue

        # Try "Category: item1, item2, item3" format
        colon_match = re.match(r"^([^:]+):\s*(.+)$", stripped)
        if colon_match:
            category = colon_match.group(1).strip()
            skill_items = [s.strip() for s in colon_match.group(2).split(",") if s.strip()]
            items.append({"category": category, "items": skill_items})
        else:
            # Treat as a single category with comma-separated items
            skill_items = [s.strip() for s in stripped.split(",") if s.strip()]
            if len(skill_items) > 1:
                items.append({"category": "Skills", "items": skill_items})
            else:
                # Single item — add to last category or create new
                if items:
                    items[-1]["items"].append(stripped)
                else:
                    items.append({"category": "Skills", "items": [stripped]})

    return items


def _parse_generic(lines: list[str]) -> list[dict]:
    """Parse a generic/unrecognized section — preserve all lines as text items."""
    items = []
    for line in lines:
        stripped = BULLET_RE.sub("", line).strip()
        if stripped:
            items.append({"text": stripped})
    return items
