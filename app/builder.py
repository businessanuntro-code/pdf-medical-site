import re


def linkify(text):
    """
    URL → link activ
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
    (17), (2,9), (1, 2, 3) → superscript
    """
    if not text:
        return ""

    pattern = r'\((\d+(?:\s*,\s*\d+)*)\)'

    def replace(match):
        content = match.group(1)
        cleaned = re.sub(r'\s+', '', content)
        cleaned = cleaned.replace(',', ', ')
        return f'<sup>{cleaned}</sup>'

    return re.sub(pattern, replace, text)


def process_inline(text):
    text = linkify(text)
    text = superscript_refs(text)
    return text


def format_content(text):
    """
    🔥 REGULA TA EXACTĂ:

    - linie cu spații la început → paragraf nou
    - linie fără spații → continuă paragraf
    """

    if not text:
        return ""

    lines = text.splitlines()

    html = []
    current_paragraph = []

    def flush():
        nonlocal current_paragraph

        if not current_paragraph:
            return ""

        paragraph_text = " ".join(current_paragraph).strip()
        paragraph_text = process_inline(paragraph_text)

        current_paragraph = []
        return f"<p>{paragraph_text}</p>"

    for line in lines:
        if not line.strip():
            # linie goală → închide paragraf
            html.append(flush())
            continue

        # detectăm indentarea reală
        has_indent = len(line) - len(line.lstrip(' ')) > 0

        cleaned = line.strip()

        if has_indent:
            # nou paragraf
            html.append(flush())
            current_paragraph = [cleaned]
        else:
            current_paragraph.append(cleaned)

    html.append(flush())

    return "\n".join([h for h in html if h])


def format_bibliography(text):
    if not text:
        return ""

    lines = text.splitlines()
    refs = [line for line in lines if line.strip()]

    html = "<ol>"

    for ref in refs:
        ref = process_inline(ref)
        html += f"<li>{ref}</li>"

    html += "</ol>"

    return html


def build_html(data):

    continut = data.get('continut_articol', '')
    continut = format_content(continut)

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
