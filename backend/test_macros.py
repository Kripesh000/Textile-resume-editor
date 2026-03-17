import re

tex = r"""
\newcommand{\resumeItem}[1]{
  \item\small{
    {#1 \vspace{-2pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeProjectHeading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & #2 \\
    \end{tabular*}\vspace{-7pt}
}
"""

def extract_macros(text):
    macros = {}
    pattern = r"\\newcommand\{\\([a-zA-Z]+)\}\[(\d+)\]"
    for match in re.finditer(pattern, text):
        macros[match.group(1)] = int(match.group(2))
    return macros

print(extract_macros(tex))
