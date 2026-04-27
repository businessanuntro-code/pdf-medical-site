import re


def linkify(text):
    if not text:
        return ""

    url_pattern = r'(https?://[^\s]+|www\.[^\s]+)'

    def replace(match):
        url = match.group(0)
        href = url if not url.startswith("www") else "https://" + url
        return f'<a href="{href}" target="_blank">{url}</a>'

    return re.sub(url_pattern, replace, text)


def superscript_refs(text):
    if not text:
        return ""

    pattern = r'\((\d+(?:\s*,\s*\d+)*)\)'

    def replace(match):
        content = match.group(1)
        cleaned = re.sub(r'\s+', '', content)
        return f'<sup>{cleaned}</sup>'

    return re.sub(pattern, replace, text)


def superscript_symbols(text):
    if not text:
        return ""
    return text.replace("™", "<sup>™</sup>").replace("®", "<sup>®</sup>")


def format_content(text):
    if not text:
        return ""

    text = text.replace("\u2029", "\n")

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    html = []

    for i, line in enumerate(lines):

        processed = linkify(line)
        processed = superscript_refs(processed)
        processed = superscript_symbols(processed)

        html.append(f"<p>{processed}</p>")

    return "\n".join(html)


def format_bibliography(text):
    if not text:
        return ""

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    html = "<ol>"
    for r in lines:
        html += f"<li>{linkify(r)}</li>"
    html += "</ol>"

    return html


def build_html(data):

    continut = format_content(data.get("continut_articol", ""))

    # 🔥 IMAGINI INJECTATE AICI
    imagini = data.get("imagini", "")

    abstract = data.get("abstract_keywords", "")
    abstract = f"<i>{superscript_symbols(superscript_refs(linkify(abstract)))}</i>"

    rezumat = data.get("rezumat_cuvinte_cheie", "")
    rezumat = f"<i>{superscript_symbols(superscript_refs(linkify(rezumat)))}</i>"

    return f"""
<!DOCTYPE html>
<html lang="ro">
<head>
<meta charset="utf-8">
<title>{data.get("titlu_ro","Articol")}</title>

<style>
body {{ font-family: Arial; margin: 40px; line-height: 1.6; }}
img {{ max-width: 100%; height: auto; }}
figure {{ text-align:center; margin:20px 0; }}
</style>
</head>

<body>

<h1>{data.get("titlu_ro","")}</h1>
<h2>{data.get("titlu_en","")}</h2>

<div><b>Autori:</b> {data.get("autori","")}</div>

<hr>

<div><h2>Abstract</h2><p>{abstract}</p></div>
<div><h2>Rezumat</h2><p>{rezumat}</p></div>

<div><h2>Conținut</h2>{continut}</div>

{imagini}   <!-- 🔥 FIX CRITIC -->

<div><h2>Bibliografie</h2>{format_bibliography(data.get("bibliografie",""))}</div>

</body>
</html>
"""
