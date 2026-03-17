import os
import json
from fastapi import HTTPException
from app.models import TemplateConfig

def get_templates_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "templates")

def list_templates() -> list[TemplateConfig]:
    """Discover all templates in the templates directory by reading their config.json."""
    templates = []
    templates_dir = get_templates_dir()
    
    if not os.path.exists(templates_dir):
        return templates

    for entry in os.scandir(templates_dir):
        if entry.is_dir() and not entry.name.startswith("__"):
            config_path = os.path.join(entry.path, "config.json")
            if os.path.isfile(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        data["id"] = entry.name # Ensure ID matches directory name
                        templates.append(TemplateConfig(**data))
                except Exception as e:
                    print(f"Warning: Failed to load template config at {config_path}: {e}")
                    
    return templates

def get_template(template_id: str) -> TemplateConfig:
    config_path = os.path.join(get_templates_dir(), template_id, "config.json")
    if not os.path.isfile(config_path):
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
        
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            data["id"] = template_id
            return TemplateConfig(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading template config: {e}")
