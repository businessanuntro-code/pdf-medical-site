from flask import Flask, render_template, request
import os
import zipfile
from lxml import etree as ET
import traceback

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================
# SAFE IDML PARSER (FIX 500)
# =========================
def parse_idml(zip_path):
    paragraphs = []

    try:
        with zipfile.ZipFile(zip_path, "r") as z:

            story_files = [
                f for f in z.namelist()
                if f.startswith("Stories/")
            ]

            for file in story_files:
                try:
                    xml = z.read(file)

                    try:
                        root = ET.fromstring(xml)
                    except Exception:
                        continue

                    # PARSE PARAGRAPHS
                    for node in root.iter():

                        if "ParagraphStyleRange" in node.tag:

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

                except Exception as e:
                    print("Story error:", file, str(e))
                    continue

    except Exception as e:
        print("ZIP ERROR:", str(e))

    return paragraphs


# =========================
# STYLE MAPPER
# =========================
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


# =========================
# HOME
# =========================
@app.route("/")
def home():
    return render_template("home.html")


# =========================
# UPLOAD + RENDER (NO SESSION, NO REDIRECT)
# =========================
@app.route("/upload", methods=["GET", "POST"])
def upload():

    try:
        if request.method == "POST":

            file = request.files["idml_file"]

            if not file:
                return "No file uploaded"

            path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(path)

            # PARSE IDML
            paragraphs = parse_idml(path)

            if not paragraphs:
                return "No content extracted from IDML"

            html = []

            for p in paragraphs:
                cls = map_style(p["style"])
                html.append(f'<div class="{cls}">{p["text"]}</div>')

            return render_template(
                "article.html",
                content="\n".join(html)
            )

        return render_template("upload.html")

    except Exception:
        print(traceback.format_exc())
        return "SERVER ERROR (check logs)"


if __name__ == "__main__":
    app.run(debug=True)
