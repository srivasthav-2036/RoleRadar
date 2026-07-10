"""
pdf_generator.py

Renders a (possibly user-edited) tailored resume JSON into an
ATS-friendly PDF using Jinja2 + WeasyPrint.
"""

import os

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

TEMPLATE_DIR = os.path.dirname(__file__)

_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


def generate_resume_pdf(tailored_resume: dict, output_path: str) -> str:
    """
    Renders tailored_resume (same schema as the extractor's resume
    JSON: name, contact, summary, skills, experience, projects,
    education, certifications, achievements, languages, domains,
    keywords) into an ATS-friendly PDF at output_path.

    Returns output_path.
    """
    template = _env.get_template("template.html")

    html_content = template.render(resume=tailored_resume)

    HTML(string=html_content, base_url=TEMPLATE_DIR).write_pdf(output_path)

    return output_path