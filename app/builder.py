import re


def format_bibliography(text):
    """
    Detectează automat referințele și le separă corect
    """

    if not text:
        return ""

    # Normalizează spațiile
    text = re.sub(r'\n+', ' ', text)

    # Split inteligent: detectează începuturi de referințe
    # bazat pe: Nume, Inițiale. (pattern comun medical)
    items = re.split(r'(?<=\.)\s+(?=[A-Z][a-zA-Z\-]+,\s?[A-Z])', text)

    # fallback dacă nu merge bine
    if len(items) < 3:
        items = re.split(r'\.\s+', text)

    # curățare
    items = [item.strip() for item in items if len(item.strip()) > 20]

    # generează HTML numerotat
    html = "<ol>"
    for item in items:
        html += f"<li>{item}</li>"
    html += "</ol>"

    return html


def build_html(data):
    """
    Builds article HTML from parsed XML data.
    Expected keys:
    - titlu_ro
    - titlu_en
    - autori
    - abstract_keywords
    - rezumat_cuvinte_cheie
    - continut_articol
    - bibliografie
    """

    return f"""
<!DOCTYPE html>
<html lang="ro">
<head>
    <meta charset="utf-8">
    <title>{data.get('titlu_ro', 'Articol')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            line-height: 1.6;
        }}
        h1 {{
            font-size: 28px;
        }}
        h2 {{
            margin-top: 30px;
            color: #222;
        }}
        .meta {{
            color: #555;
            margin-bottom: 20px;
        }}
        .section {{
            margin-bottom: 25px;
        }}
        ol {{
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 12px;
        }}
    </style>
</head>
<body>

    <!-- TITLU RO -->
    <h1>{data.get('titlu_ro', '')}</h1>

    <!-- TITLU EN -->
    <h2>{data.get('titlu_en', '')}</h2>

    <!-- AUTORI -->
    <div class="meta">
        <b>Autori:</b> {data.get('autori', '')}
    </div>

    <hr>

    <!-- ABSTRACT + KEYWORDS -->
    <div class="section">
        <h2>Abstract & Keywords</h2>
        <p>{data.get('abstract_keywords', '')}</p>
    </div>

    <!-- REZUMAT + CUVINTE CHEIE -->
    <div class="section">
        <h2>Rezumat și Cuvinte Cheie</h2>
        <p>{data.get('rezumat_cuvinte_cheie', '')}</p>
    </div>

    <!-- CONTINUT ARTICOL -->
    <div class="section">
        <h2>Conținut articol</h2>
        <div>
            {data.get('continut_articol', '')}
        </div>
    </div>

    <!-- BIBLIOGRAFIE -->
    <div class="section">
        <h2>Bibliografie</h2>
        {format_bibliography(data.get('bibliografie', ''))}
    </div>

</body>
</html>
"""
