from typing import Any, Optional
from pydantic import BaseModel

class ParsedLine(BaseModel):
    text: str
    line_number: int
    font_size: float = 11.0
    is_bold: bool = False
    is_italic: bool = False
    indent_level: int = 0  # 0, 1, 2... based on xndent relative to page margins
    x_position: float = 0.0
    y_position: float = 0.0
    is_heading_candidate: bool = False

class NormalizedDocument(BaseModel):
    lines: list[ParsedLine]
    raw_source_type: str  # "pdf" or "latex"
    source_metadata: dict[str, Any] = {}
