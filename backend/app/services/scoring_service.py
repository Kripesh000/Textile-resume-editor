from typing import Any, Optional
import re
from app.schemas.normalizer_models import ParsedLine, NormalizedDocument
from app.services.parsing_rules import SECTION_PATTERNS

class ScoringEngine:
    def __init__(self):
        self.section_keywords = SECTION_PATTERNS

    def score_document(self, doc: NormalizedDocument) -> list[dict[str, Any]]:
        """Assign confidence scores to lines for being section headings."""
        results = []
        for i, line in enumerate(doc.lines):
            scores = self.score_line(line, doc.lines[i-1] if i > 0 else None)
            results.append({
                "line_idx": line.line_number,
                "text": line.text,
                "scores": scores,
                "primary_type": self._get_primary_type(scores),
                "max_score": max(scores.values()) if scores else 0.0
            })
        return results

    def score_line(self, line: ParsedLine, prev_line: Optional[ParsedLine]) -> dict[str, float]:
        """
        Calculate confidence scores for each section type.
        Returns a dict: {"experience": 0.8, "education": 0.1, ...}
        """
        scores = {stype: 0.0 for stype in self.section_keywords.keys()}
        scores["generic"] = 0.0
        
        text = line.text.strip().lower()
        if not text or len(text) > 60:
            return scores

        # 1. Keyword Signals (Strong)
        for stype, pattern in self.section_keywords.items():
            if pattern.match(text):
                scores[stype] += 0.7
            elif any(kw in text for kw in self._get_keywords(stype)):
                scores[stype] += 0.3

        # 2. Formatting Signals (Medium)
        if line.is_bold:
            for stype in scores: scores[stype] += 0.15
        if line.text.isupper():
            for stype in scores: scores[stype] += 0.15
        
        # 3. Position Signals
        if line.indent_level == 0:
            for stype in scores: scores[stype] += 0.1
            
        # 4. Contextual Signals (Relative to prev line)
        if prev_line:
            # If font size increased or formatting changed significantly
            if line.font_size > prev_line.font_size:
                for stype in scores: scores[stype] += 0.1
            if line.is_bold and not prev_line.is_bold:
                for stype in scores: scores[stype] += 0.1

        # Clip scores at 1.0
        return {k: min(v, 1.0) for k, v in scores.items()}

    def _get_primary_type(self, scores: dict[str, float]) -> str:
        if not scores: return "none"
        max_type = max(scores, key=scores.get)
        if scores[max_type] < 0.1: return "none"
        return max_type

    def _get_keywords(self, stype: str) -> list[str]:
        # Mapping from parsing_rules or expanded
        mapping = {
            "experience": ["work", "experience", "employment", "history", "career", "internship"],
            "education": ["education", "academic", "university", "college", "degree"],
            "project": ["project", "hackathon", "personal", "built", "developed"],
            "skills": ["skill", "technical", "languages", "frameworks", "tools"]
        }
        return mapping.get(stype, [])

def get_scoring_engine():
    return ScoringEngine()
