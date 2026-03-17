import asyncio
from app.services.latex_service import render_template

data = {
    "header": {
        "name": "Test Name",
        "email": "test@example.com",
        "phone": "1234567890",
    },
    "sections": [
        {
            "title": "Education",
            "section_type": "education",
            "items": [
                {
                    "institution": "University of Central Florida",
                    "degree": "B.S. in Computer Science",
                    "start_date": "Aug 2019",
                    "end_date": "May 2023",
                }
            ]
        }
    ]
}

tex = render_template('user_deaaa872-f844-4279-b252-a78c33055d2c', data)
with open('test_out.tex', 'w') as f:
    f.write(tex)

import subprocess
res = subprocess.run(['tectonic', 'test_out.tex'], capture_output=True, text=True)
print(res.stdout)
print(res.stderr)
