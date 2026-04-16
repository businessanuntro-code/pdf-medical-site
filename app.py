from flask import Flask, render_template, request
import os, zipfile
from lxml import etree as ET

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# -------------------------
# PARSE IDML STRUCTURE
# -------------------------
def parse_idml(zip_path):
    paragraphs = []

    with zipfile.ZipFile(zip_path, "r") as z:
        story_files = [f for f in z.namelist() if f.startswith("Stories/")]

        for file in story_files:
            xml = z.read(file)

            try:
                root = ET.fromstring(xml)
            except:
                continue

            for node in root.iter():

                if node.tag.endswith("ParagraphStyleRange"):
                    text_parts = []

                    for t in node.iter():
                        if t.text and t.text.strip():
                            text_parts.append(t.text.strip())

                    text = " ".join(text_parts).strip()

                    if text:
                        style = node.attrib.get("AppliedParagraphStyle", "")
                        paragraphs.append({
                            "text": text,
                            "style": style
                        })

    return paragraphs


# -------------------------
# STYLE MAPPER
# -------------------------
def map_style(style):
    s = style.lower()

    if "title" in s:
        return "title"
    if "author" in s:
        return "authors"
    if "abstract" in s:
        return "abstract"
    if "heading" in s:
        return "heading"
    if "caption" in s:
        return "caption"

    return "body"


# -------------------------
# HOME
# -------------------------
@app.route("/")
def home():
    return render_template("home.html")


# -------------------------
# UPLOAD + RENDER
# -------------------------
@app.route("/upload", methods=["GET", "POST"])
def upload():

    if request.method == "POST":
        file = request.files["idml_file"]

        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        paragraphs = parse_idml(path)

        html = []

        for p in paragraphs:
            cls = map_style(p["style"])
            html.append(f'<div class="{cls}">{p["text"]}</div>')

        return render_template("article.html", content="\n".join(html))

    return render_template("upload.html")


if __name__ == "__main__":
    app.run(debug=True)
