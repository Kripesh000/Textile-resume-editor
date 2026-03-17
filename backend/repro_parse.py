import asyncio
import json
from app.services.latex_parser_service import _extract_data, _generate_template_deterministically

tex = r"""
\documentclass[letterpaper,11pt]{article}
\begin{document}
\begin{center}
    \textbf{\Huge \scshape Pratyush Khanal} \\ \vspace{1pt}
    \small Nashville, TN $|$
    \small 615-892-4619 $|$ \href{mailto:pratyushkhanal95@gmail.com}{\underline{pratyushkhanal95@gmail.com}} $|$ 
    \href{https://www.linkedin.com/in/pratyushkhanal/}{\underline{Linkedin}} $|$
    \href{https://github.com/Khanalpratyush}{\underline{Github}}
\end{center}

\section{Education}
  \resumeSubHeadingListStart
    \resumeSubheading
      {Fisk University}{Nashville, TN}
      {Bachelor of Science in Computer Science}{\textbf{Expected Graduation: May 2026}}
  \resumeSubHeadingListEnd

\section{Technical Skills}
 \begin{itemize}[leftmargin=0.15in, label={}]
    \small{\item{
     \textbf{Programming Languages}{: Java, Python, C/C++, SQL (Postgres), JavaScript, TypeScript, HTML5/CSS3, R} \\
     \textbf{Frameworks}{: React, Node.js, Next.js, Flask, FastAPI} \\
    }}
 \end{itemize}

\section{Experience}
  \resumeSubHeadingListStart
    \resumeSubheading
      {Software Development Engineer Intern}{May 2025 – August 2025}
      {\textbf{Amazon}}{Cupertino, CA}
      \resumeItemListStart
        \resumeItem{Developed an LLM powered \textbf{syslog summarizer}}
      \resumeItemListEnd
  \resumeSubHeadingListEnd
\end{document}
"""

data = _extract_data(tex)
print("EXTRACTED DATA:")
print(json.dumps(data, indent=2))

template = _generate_template_deterministically(tex, data)
print("\nGENERATED TEMPLATE:")
print(template)
