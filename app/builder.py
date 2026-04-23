import re


def format_bibliography(text):
    """
    Separă bibliografia după 1. 2. 3. etc
    """

    if not text:
        return ""

    # normalizează
    text = text.replace("\n", " ")

    # split după 1. 2. 3.
    items = re.split(r'\s*(\d+\.)\s*', text)

    refs = []
    current = ""

    for part in items:
        part = part.strip()

        if not part:
            continue

        # dacă e număr (ex: "1.")
        if re.match(r'^\d+\.$', part):
            if current:
                refs.append(current.strip())
            current = part  # începe nouă referință
        else:
            current += " " + part

    if current:
        refs.append(current.strip())

    # HTML list
    html = "<ol>"
    for ref in refs:
        # eliminăm numărul din text (pentru că <ol> îl pune automat)
        ref = re.sub(r'^\d+\.\s*', '', ref)
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
