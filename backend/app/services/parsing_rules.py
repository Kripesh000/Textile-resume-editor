"""Rules and utilities for categorizing and splitting resume sections deterministically."""

import re

# Section heading patterns (case-insensitive)
SECTION_PATTERNS = {
    "experience": re.compile(
        r"^(work\s+experience|professional\s+experience|relevant\s+experience"
        r"|experience|employment(\s+history)?|internship(s)?"
        r"|work\s+history|industry\s+experience|career\s+history|leadership|volunteer)\s*$",
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

# Generic Keywords used for splitting mixed titles
KEYWORD_MAPPING = {
    "experience": ["experience", "employment", "work", "internship", "leadership", "volunteer", "activit", "history", "career"],
    "education": ["education", "academic", "degree", "course", "certific", "university", "college"],
    "project": ["project", "hackathon", "research", "publication", "open source"],
    "skills": ["skill", "competenc", "technolog", "tool", "programming", "expertise"]
}


def detect_section_type(title: str) -> str | None:
    """Detect section type from a known pattern."""
    cleaned = title.strip().rstrip(":")
    # Perfect match check
    for section_type, pattern in SECTION_PATTERNS.items():
        if pattern.match(cleaned):
            return section_type
    
    # Try splitting for mixed titles (e.g. "Hackathons and Experience")
    # If the title isn't a direct match, check if it's mixed but we take the first type we find as a fallback
    return None

def determine_primary_type(title: str) -> str:
    """Fallback keyword check to guess a type if strict regex fails."""
    lower_title = title.lower()
    for stype, keywords in KEYWORD_MAPPING.items():
        if any(kw in lower_title for kw in keywords):
            return stype
    return "generic"


def _convert_generic_items(section_type: str, items: list[dict]) -> list[dict]:
    """Convert generic {text:...} items to the expected format for a given section type.
    Used by split_mixed_section to ensure the items conform to the schema."""
    converted = []
    for item in items:
        text = item.get("text", "")
        
        # If the item is already structured, don't overwrite it with a generic shell
        has_structured_fields = any(k in item for k in [
            "company", "role", "institution", "degree", "name", "category", "tech_stack"
        ])
        
        if not text or has_structured_fields:
            # If it already has other keys (e.g., from PDF parser), keep it
            # But ensure it's not JUST {'text': ...}
            if len(item) > 1 or "text" not in item or has_structured_fields:
                converted.append(item)
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
            # Very important: ensure Skills output an array!
            converted.append({"category": "Skills", "items": [s.strip() for s in text.split(",") if s.strip()]})
        else:
            converted.append(item)
    return converted


def split_mixed_section(title: str, items: list[dict]) -> list[dict]:
    """
    Given a list of items from a section and the section title, determine if it's a mixed section
    (e.g., 'Projects & Experience'). If so, attempt to separate items into appropriate section blocks.
    Returns a list of section dicts: [{"section_type": "...", "title": "...", "items": [...]}]
    """
    lower_title = title.lower()
    
    # Split tokens like 'and', '&', '|'
    parts = re.split(r'\s+(?:and|&|\|)\s+', lower_title)
    
    types_found = []
    titles_mapped = {}
    
    for part in parts:
        ptype = determine_primary_type(part)
        if ptype not in types_found and ptype != "generic":
            types_found.append(ptype)
            titles_mapped[ptype] = part.title()

    if len(types_found) < 2:
        # Not a mixed section or cannot be split confidently.
        ptype = determine_primary_type(title)
        converted_items = _convert_generic_items(ptype, items)
        return [{"section_type": ptype, "title": title, "items": converted_items}]

    # We have a mixed section (e.g. Projects and Experience). We need to classify each item.
    sections_out = {t: {"section_type": t, "title": titles_mapped[t], "items": []} for t in types_found}
    generic_out = []
    
    for item in items:
        # Heuristics for item type based on parsed fields
        # This assumes item was parsed initially via some generic or primary parser
        # Usually from PDF parsing, it might have company/role (experience) or name/tech_stack (project)
        
        # If it's already structured:
        if "company" in item or "role" in item:
            # It looks like experience
            if "experience" in sections_out:
                sections_out["experience"]["items"].append(item)
            else:
                generic_out.append(item)
        elif "tech_stack" in item or "url" in item or "name" in item:
            # It looks like project
            if "project" in sections_out:
                sections_out["project"]["items"].append(item)
            else:
                generic_out.append(item)
        elif "institution" in item or "degree" in item:
            if "education" in sections_out:
                sections_out["education"]["items"].append(item)
            else:
                generic_out.append(item)
        elif "category" in item:
             if "skills" in sections_out:
                 sections_out["skills"]["items"].append(item)
             else:
                 generic_out.append(item)
        elif "text" in item and "skills" in types_found:
             # Convert generic {text: "..."} into proper SkillItem with string array
             text = item.get("text", "")
             category_item = {"category": "Skills", "items": [s.strip() for s in text.split(",")]}
             sections_out["skills"]["items"].append(category_item)
        else:
            # Maybe it's generic {text: "..."}. We have to guess from the text.
            text = item.get("text", "").lower()
            if "experience" in types_found and any(kw in text for kw in ["intern", "developer", "engineer", "worked"]):
                sections_out["experience"]["items"].append(item)
            elif "project" in types_found and any(kw in text for kw in ["hackathon", "built", "app", "created"]):
                sections_out["project"]["items"].append(item)
            else:
                # Default to the first type found
                sections_out[types_found[0]]["items"].append(item)

    # Filter out empty sections
    result = [s for s in sections_out.values() if s["items"]]
    if generic_out:
        if result:
            result[0]["items"].extend(generic_out)
        else:
            result.append({"section_type": types_found[0], "title": title, "items": generic_out})
            
    # Apply format converter so we don't leak {"text": "..."} to the frontend for strictly typed sections
    for sec in result:
        sec["items"] = _convert_generic_items(sec["section_type"], sec["items"])

    return result
