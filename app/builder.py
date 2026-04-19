def format_bibliography(text):
    """
    Transformă textul brut în listă HTML (o referință pe linie)
    """
    if not text:
        return ""

    import re

    # separă după numere (1. 2. 3.) sau newline
    items = re.split(r'\n|\d+\.\s', text)

    # curățare
    items = [item.strip() for item in items if item.strip()]

    # generează HTML list
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
            margin-bottom: 10px;
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
