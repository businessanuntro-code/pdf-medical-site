import re


def linkify(text):
    """
    Transformă URL-urile în linkuri HTML active
    """
    if not text:
        return ""

    url_pattern = r'(https?://[^\s]+|www\.[^\s]+)'

    def replace(match):
        url = match.group(0)

        href = url
        if url.startswith("www"):
            href = "https://" + url

        return f'<a href="{href}" target="_blank">{url}</a>'

    return re.sub(url_pattern, replace, text)


def superscript_refs(text):
    """
    Transformă:
    (17) → <sup>17</sup>
    (2,9) → <sup>2,9</sup>
    (1, 2, 3) → <sup>1, 2, 3</sup>
    """

    if not text:
        return ""

    # 🔥 prinde orice conținut numeric (cu virgule și spații) în paranteze
    pattern = r'\((\d+(?:\s*,\s*\d+)*)\)'

    def replace(match):
        content = match.group(1)

        # curăță spațiile din interior dar păstrează virgulele logice
        cleaned = re.sub(r'\s+', '', content)
        cleaned = cleaned.replace(',', ', ')  # normalizare frumoasă

        return f'<sup>{cleaned}</sup>'

    return re.sub(pattern, replace, text)


def format_bibliography(text):
    """
    Bibliografie pe linii + linkuri active + superscript
    """

    if not text:
        return ""

    lines = text.splitlines()
    refs = [line.strip() for line in lines if line.strip()]

    html = "<ol>"

    for ref in refs:
        ref = linkify(ref)
        ref = superscript_refs(ref)
        html += f"<li>{ref}</li>"

    html += "</ol>"

    return html


def build_html(data):
    """
    Builds article HTML from parsed XML data.
    """

    continut = data.get('continut_articol', '')
    continut = linkify(continut)
    continut = superscript_refs(continut)

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
        sup {{
            font-size: 0.75em;
            vertical-align: super;
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
            {continut}
        </div>
    </div>

    <div class="section">
        <h2>Bibliografie</h2>
        {format_bibliography(data.get('bibliografie', ''))}
    </div>

</body>
</html>
"""
