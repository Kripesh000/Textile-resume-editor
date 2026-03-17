import os
import re
import subprocess
import tempfile

import jinja2

from app.config import settings

LATEX_SPECIAL_CHARS = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}

ESCAPE_PATTERN = re.compile("|".join(re.escape(k) for k in LATEX_SPECIAL_CHARS))


def escape_latex(text: str) -> str:
    if not text:
        return ""
    return ESCAPE_PATTERN.sub(lambda m: LATEX_SPECIAL_CHARS[m.group()], text)


templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")

latex_env = jinja2.Environment(
    block_start_string=r"\BLOCK{",
    block_end_string="}",
    variable_start_string=r"\VAR{",
    variable_end_string="}",
    comment_start_string=r"\#{",
    comment_end_string="}",
    line_statement_prefix="%%j2",
    line_comment_prefix="%#",
    trim_blocks=True,
    autoescape=False,
    loader=jinja2.FileSystemLoader(os.path.abspath(templates_dir)),
)
latex_env.filters["escape_latex"] = escape_latex


def render_template(template_key: str, data: dict) -> str:
    # Try directory-based structure first (e.g., jake_classic/template.tex.j2)
    try:
        template = latex_env.get_template(f"{template_key}/template.tex.j2")
    except jinja2.TemplateNotFound:
        # Fallback to flat-file structure (e.g., custom.tex.j2)
        try:
            template = latex_env.get_template(f"{template_key}.tex.j2")
        except jinja2.TemplateNotFound:
            raise jinja2.TemplateNotFound(f"Template '{template_key}' not found in directory or flat-file format.")
            
    return template.render(**data)


async def compile_pdf(tex_content: str) -> bytes:
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "resume.tex")
        pdf_path = os.path.join(tmpdir, "resume.pdf")

        with open(tex_path, "w") as f:
            f.write(tex_content)

        result = subprocess.run(
            [settings.tectonic_path, tex_path],
            capture_output=True,
            timeout=30,
            cwd=tmpdir,
        )

        if result.returncode != 0:
            error_msg = result.stderr.decode("utf-8", errors="replace")
            raise RuntimeError(f"LaTeX compilation failed: {error_msg}")

        with open(pdf_path, "rb") as f:
            return f.read()
