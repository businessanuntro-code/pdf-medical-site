import re


def format_bibliography(text):
    """
    Reface referințele care sunt sparte pe mai multe rânduri
    """

    if not text:
        return ""

    lines = text.splitlines()

    refs = []
    current_ref = ""

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # detectează început de referință (Nume + inițiale)
        if re.match(r'^[A-Z][a-zA-Z\-]+ [A-Z]{1,3},', line):
            # salvează referința anterioară
            if current_ref:
                refs.append(current_ref.strip())
            current_ref = line
        else:
            # continuare referință
            current_ref += " " + line

    # adaugă ultima
    if current_ref:
        refs.append(current_ref.strip())

    # generează HTML
    html = "<ol>"
    for ref in refs:
        html += f"<li>{ref}</li>"
    html += "</ol>"

    return html


def build_html(data):
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

    <h1>{data.get('titlu_ro', '')}</h1>
    <h2>{data.get('titlu_en', '')}</h2>

    <div class="meta">
        <b>Autori:</b> {data.get('autori', '')}
    </div>

    <hr>

    <div class="section">
        <h2>Abstract & Keywords</h2>
        <p>{data.get('abstract_keywords', '')}</p>
    </div>

    <div class="section">
        <h2>Rezumat și Cuvinte Cheie</h2>
        <p>{data.get('rezumat_cuvinte_cheie', '')}</p>
    </div>

    <div class="section">
        <h2>Conținut articol</h2>
        <div>
            {data.get('continut_articol', '')}
        </div>
    </div>

    <div class="section">
        <h2>Bibliografie</h2>
        {format_bibliography(data.get('bibliografie', ''))}
    </div>

</body>
</html>
"""
