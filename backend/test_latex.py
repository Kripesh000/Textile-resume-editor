import asyncio
import json
from app.services.latex_parser_service import parse_latex

test_latex = r"""
\documentclass[letterpaper,11pt]{article}
\begin{document}

\textbf{\Huge \scshape John Doe}
\href{mailto:john@example.com}{john@example.com}
\href{https://linkedin.com/in/johndoe}{linkedin.com/in/johndoe}

\section{Experience}
  \resumeSubheading
    {Amazon}{Cupertino, CA}
    {SDE Intern}{May 2025}
    \resumeItemListStart
        \resumeItem{Developed a scalable microservice}
        \resumeItem{Improved latency by 20\%}
    \resumeItemListEnd

\section{Projects}
    \resumeProjectHeading
        {\textbf{Portfolio Website} $|$ \emph{React, Next.js, Tailwind}}{Jan 2024}
        \resumeItemListStart
            \resumeItem{Built a responsive portfolio}
            \resumeItem{Deployed on Vercel}
        \resumeItemListEnd

\end{document}
"""


async def main():
    result = await parse_latex(test_latex)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
