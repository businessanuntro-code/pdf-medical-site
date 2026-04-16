
from flask import Flask, render_template, request
import os, zipfile
from lxml import etree as ET

app = Flask(__name__)
BASE_DIR = os.getcwd()
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def parse_styles(zipf):
    style_file = "Resources/Styles.xml"
    if style_file not in zipf.namelist():
        return ""
    try:
        root = ET.fromstring(zipf.read(style_file))
        css = []
        for elem in root.iter():
            name = elem.attrib.get("Self", "")
            if "ParagraphStyle" in name:
                cls = name.replace("ParagraphStyle/", "").replace(" ", "_")
                css.append(f".{cls} {{ font-size:12pt; line-height:1.6; margin-bottom:8px; }}")
        return "\\n".join(css)
    except Exception:
        return ""

def extract_story_blocks(zipf):
    blocks = []
    for file in zipf.namelist():
        if file.startswith("Stories/") and file.endswith(".xml"):
            try:
                root = ET.fromstring(zipf.read(file))
                txt = []
                for elem in root.iter():
                    if elem.text and elem.text.strip():
                        txt.append(elem.text.strip())
                if txt:
                    blocks.append(" ".join(txt))
            except Exception:
                continue
    return blocks

def generate_from_path(path):
    try:
        with zipfile.ZipFile(path, "r") as z:
            blocks = extract_story_blocks(z)
            dynamic_css = parse_styles(z)
    except Exception as e:
        return f"Processing error: {str(e)}", 500

    html = []
    for i, block in enumerate(blocks):
        cls = "body"
        if i == 0: cls = "title"
        elif i == 1: cls = "authors"
        html.append(f'<div class="{cls}">{block}</div>')

    return render_template("article.html", content="\\n".join(html), dynamic_css=dynamic_css)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/upload", methods=["GET","POST"])
def upload():
    if request.method == "POST":
        file = request.files.get("idml_file")
        if not file or not file.filename:
            return "No file selected", 400
        filename = os.path.basename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        return generate_from_path(path)
    return render_template("upload_idml.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
