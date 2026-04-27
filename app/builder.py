import re


def linkify(text):
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
    if not text:
        return ""

    pattern = r'\((\d+(?:\s*,\s*\d+)*)\)'

    def replace(match):
        content = match.group(1)
        cleaned = re.sub(r'\s+', '', content)
        cleaned = cleaned.replace(',', ', ')
        return f'<sup>{cleaned}</sup>'

    return re.sub(pattern, replace, text)


def superscript_symbols(text):
    if not text:
        return ""

    text = text.replace("™", "<sup>™</sup>")
    text = text.replace("®", "<sup>®</sup>")
    return text


# =========================
# FIX STABIL: detectare HTML real
# =========================
def is_html(text):
    if not text:
        return False

    return any(tag in text for tag in ["<img", "<figure", "<table", "<a ", "<sup"])


def format_content(text):
    """
    REGULA FINALĂ:
    - dacă vine HTML din parser → NU îl modificăm
    - dacă e text simplu → îl procesăm
    """

    if not text:
        return ""

    text = text.replace("\u2029", "\n")

    # 🔥 IMPORTANT: NU strica HTML-ul din parser
    if is_html(text):
        return text

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    html = []

    for i, line in enumerate(lines):

        processed = linkify(line)
        processed = superscript_refs(processed)
        processed = superscript_symbols(processed)

        words = line.split()
        word_count = len(words)

        next_is_long = False
        if i + 1 < len(lines):
            next_words = lines[i + 1].split()
            if len(next_words) > 8:
                next_is_long = True

        if 1 <= word_count <= 5 and next_is_long:
            html.append(f"<p><b>{processed}</b></p>")
        else:
            html.append(f"<p>{processed}</p>")

    return "\n".join(html)


def format_bibliography(text):
    if not text:
        return ""

    lines = text.splitlines()
    refs = [line.strip() for line in lines if line.strip()]

    html = "<ol>"

    for ref in refs:
        ref = linkify(ref)
        html += f"<li>{ref}</li>"

    html += "</ol>"

    return html


def build_html(data):

    continut = data.get('continut_articol', '')
    continut = format_content(continut)

    abstract = data.get('abstract_keywords', '')
    abstract = linkify(abstract)
    abstract = superscript_refs(abstract)
    abstract = superscript_symbols(abstract)
    abstract = f"<i>{abstract}</i>" if abstract else ""

    rezumat = data.get('rezumat_cuvinte_cheie', '')
    rezumat = linkify(rezumat)
    rezumat = superscript_refs(rezumat)
    rezumat = superscript_symbols(rezumat)
    rezumat = f"<i>{rezumat}</i>" if rezumat else ""

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
            background: #f7f7f7;
        }}

        .container {{
            background: white;
            padding: 30px;
            max-width: 900px;
            margin: auto;
        }}

        h1 {{
            font-size: 28px;
            color: #222;
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

        p {{
            margin: 0 0 10px 0;
            text-align: justify;
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

        /* 🔥 IMAGINI FIX FINAL */
        img {{
            max-width: 100%;
            display: block;
            margin: 20px auto;
        }}

        figure {{
            margin: 20px 0;
            text-align: center;
        }}
    </style>
</head>

<body>

<div class="container">

    <h1>{data.get('titlu_ro', '')}</h1>
    <h2>{data.get('titlu_en', '')}</h2>

    <div class="meta">
        <b>Autori:</b> {data.get('autori', '')}
    </div>

    <hr>

    <div class="section">
        <h2>Abstract & Keywords</h2>
        <p>{abstract}</p>
    </div>

    <div class="section">
        <h2>Rezumat și Cuvinte Cheie</h2>
        <p>{rezumat}</p>
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

</div>

</body>
</html>
"""
