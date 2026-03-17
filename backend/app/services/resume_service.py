from app.models import Profile, ResumeVariant, SectionConfig

def build_render_data(profile: Profile, variant: ResumeVariant, template_config: dict) -> dict:
    """Builds a flat dictionary to be passed to the Jinja2 LaTeX template.
    
    This function applies the ResumeVariant query (which selects specific items and defines section order)
    to the master Profile to produce the exact data needed for rendering.
    """
    data = {
        "header_data": {
            "name": profile.name,
            "email": profile.email,
            "phone": profile.phone,
            "linkedin": profile.linkedin,
            "github": profile.github,
            "website": profile.website,
        },
        "config": template_config,
        "sections": []
    }

    # Filter data based on variant selection
    selected_exps = [e for e in profile.experiences if e.id in variant.selected_experience_ids]
    selected_projs = [p for p in profile.projects if p.id in variant.selected_project_ids]
    
    # Filter bullets inside selected experiences and projects
    for exp in selected_exps:
        exp.bullets = sorted(
            [b for b in exp.bullets if b.id in variant.selected_bullet_ids],
            key=lambda x: x.order
        )
    for proj in selected_projs:
        proj.bullets = sorted(
            [b for b in proj.bullets if b.id in variant.selected_bullet_ids],
            key=lambda x: x.order
        )

    selected_skills = [s for s in profile.skill_categories if s.id in variant.selected_skill_category_ids]

    # Map section titles to their filtered data
    section_map = {
        "Experience": {
            "title": "Experience",
            "type": "experience",
            "section_type": "experience",
            "entries": [e.model_dump() for e in selected_exps]
        },
        "Projects": {
            "title": "Projects",
            "type": "project",
            "section_type": "projects",
            "entries": [p.model_dump() for p in selected_projs]
        },
        "Education": {
            "title": "Education",
            "type": "education",
            "section_type": "education",
            "entries": [e.model_dump() for e in profile.education]
        },
        "Skills": {
            "title": "Skills",
            "type": "skills",
            "section_type": "skills",
            "entries": [s.model_dump() for s in selected_skills]
        }
    }
    
    # Apply legacy overrides from variant.sections if present (for live preview of editor-only edits)
    if variant.sections:
        for v_sec in variant.sections:
            v_title = v_sec.get("title")
            # If the section matches a known category, override its entries
            target = None
            if v_title in section_map:
                target = section_map[v_title]
            else:
                # Search by type if title doesn't match exactly
                v_type = v_sec.get("section_type")
                target = next((s for s in section_map.values() if s["type"] == v_type), None)
            
            if target:
                # Map legacy 'items' or 'entries' to 'entries'
                raw_items = v_sec.get("items") or v_sec.get("entries") or []
                # Flatten items if they are in the {id, data} format
                mapped = []
                for i in raw_items:
                    item_data = i["data"] if isinstance(i, dict) and "data" in i else i
                    # Ensure bullets/items exist for templates
                    if target["type"] in ["experience", "project"] and "bullets" not in item_data:
                        item_data["bullets"] = []
                    if target["type"] == "skills" and "items" not in item_data:
                        item_data["items"] = []
                    mapped.append(item_data)
                target["entries"] = mapped
            else:
                # Add it as a generic section
                raw_items = v_sec.get("items") or v_sec.get("entries") or []
                mapped = []
                for i in raw_items:
                    item_data = i["data"] if isinstance(i, dict) and "data" in i else i
                    if "bullets" not in item_data:
                        item_data["bullets"] = []
                    mapped.append(item_data)
                
                new_sec = {
                    "title": v_title,
                    "type": v_sec.get("section_type", "generic"),
                    "section_type": v_sec.get("section_type", "generic"),
                    "entries": mapped
                }
                section_map[v_title] = new_sec
                # Make sure it gets ordered at the end if not in orders
                if not any(o.title == v_title for o in variant.section_order or []):
                    if not variant.section_order:
                        variant.section_order = []
                    variant.section_order.append(SectionConfig(title=v_title, order=len(variant.section_order)))
    # If no section order is defined, provide a default one
    orders = variant.section_order
    if not orders:
        orders = [
            SectionConfig(title="Experience", order=0),
            SectionConfig(title="Projects", order=1),
            SectionConfig(title="Education", order=2),
            SectionConfig(title="Skills", order=3),
        ]

    # Build ordered sections based on variant config
    for sec_config in orders:
        if sec_config.title in section_map:
            sec_data = section_map[sec_config.title]
            if sec_data["entries"]: # Only include non-empty sections
                data["sections"].append(sec_data)

    return data
