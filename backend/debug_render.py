import jinja2
import os

LATEX_SPECIAL_CHARS = {"&": r"\&"}
def escape_latex(text: str) -> str: return text

templates_dir = "/Users/pratyushkhanal/resumeeditor/backend/app/templates"
latex_env = jinja2.Environment(
    block_start_string=r"\BLOCK{",
    block_end_string="}",
    variable_start_string=r"\VAR{",
    variable_end_string="}",
    loader=jinja2.FileSystemLoader(os.path.abspath(templates_dir)),
)

DUMMY_DATA = {
    "header_data": {"name": "Test"},
    "sections": [{"title": "Education", "entries": []}]
}

try:
    template = latex_env.get_template("modern_sidebar/template.tex.j2")
    print("Template loaded")
    output = template.render(**DUMMY_DATA)
    print("Rendered successfully")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
