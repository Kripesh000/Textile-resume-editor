import io
import re
from typing import Any
import pdfplumber
from app.schemas.normalizer_models import ParsedLine, NormalizedDocument

def normalize_pdf(file_bytes: bytes) -> NormalizedDocument:
    """Normalize PDF into a list of ParsedLine objects."""
    lines = []
    line_idx = 0
    
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            # Extract words with positional metadata
            words = page.extract_words(
                x_tolerance=3, 
                y_tolerance=3, 
                keep_blank_chars=True, 
                use_text_flow=True
            )
            
            if not words:
                continue

            # Group words into lines by top position
            current_line_words = []
            last_top = None
            
            for word in words:
                if last_top is None or abs(word["top"] - last_top) < 3:
                    current_line_words.append(word)
                    last_top = word["top"]
                else:
                    # Flush current line
                    lines.append(_create_parsed_line(current_line_words, line_idx, page))
                    line_idx += 1
                    current_line_words = [word]
                    last_top = word["top"]
            
            if current_line_words:
                lines.append(_create_parsed_line(current_line_words, line_idx, page))
                line_idx += 1

    return NormalizedDocument(
        lines=lines,
        raw_source_type="pdf",
        source_metadata={"page_count": len(pdf.pages) if 'pdf' in locals() else 0}
    )

def _create_parsed_line(words: list[dict], idx: int, page: Any) -> ParsedLine:
    """Helper to convert a group of words into a ParsedLine."""
    text = " ".join(w["text"] for w in words).strip()
    
    # Get average font size and detect styles from the first word or majority
    # (Simplified: take first word's stats)
    first_word = words[0]
    
    # Heuristic for indent level: round x0 to nearest 0.25 inch (approx 18 points)
    # Using 72 points per inch standard.
    indent_level = int(round(first_word["x0"] / 18))
    
    return ParsedLine(
        text=text,
        line_number=idx,
        font_size=float(first_word.get("size", 11.0)),
        is_bold="Bold" in first_word.get("fontname", ""),
        is_italic="Italic" in first_word.get("fontname", ""),
        indent_level=indent_level,
        x_position=float(first_word["x0"]),
        y_position=float(first_word["top"])
    )

def normalize_latex(tex_content: str) -> NormalizedDocument:
    """Normalize LaTeX into a list of ParsedLine objects."""
    lines = []
    raw_lines = tex_content.split("\n")
    
    for i, line in enumerate(raw_lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("%"):
            continue
            
        # Very basic LaTeX cleaning for normalization
        # We want to keep signals like \section
        is_heading = False
        if r"\section" in line or r"\subsection" in line:
            is_heading = True
        
        # Strip most common commands but keep content
        clean_text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\{([^}]*)\}", r"\1", stripped)
        clean_text = re.sub(r"\\[a-zA-Z]+", " ", clean_text)
        clean_text = re.sub(r"[{}]", "", clean_text)
        clean_text = re.sub(r"\s+", " ", clean_text).strip()
        
        if not clean_text:
            continue
            
        lines.append(ParsedLine(
            text=clean_text,
            line_number=i,
            indent_level=len(line) - len(line.lstrip()),
            is_heading_candidate=is_heading
        ))
        
    return NormalizedDocument(
        lines=lines,
        raw_source_type="latex"
    )
