from flask import Flask, render_template, request, redirect, url_for, session
import os, zipfile
from lxml import etree as ET

app = Flask(__name__)
app.secret_key = "supersecret"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def parse_styles(zipf):
    css = []
    style_file = "Resources/Styles.xml"
    if style_file not in zipf.namelist():
        return ""
    root = ET.fromstring(zipf.read(style_file))
    for elem in root.iter():
        name = elem.attrib.get("Self", "")
        if "ParagraphStyle" in name:
            cls = name.replace("ParagraphStyle/", "").replace(" ", "_")
            css.append(f".{cls} { font-size: 12pt; line-height: 1.6; margin-bottom: 8px; }")
    return "\n".join(css)

def extract_story_blocks(zipf):
    blocks = []
    for file in zipf.namelist():
        if file.startswith("Stories/") and file.endswith(".xml"):
            root = ET.fromstring(zipf.read(file))
            texts = []
            for elem in root.iter():
                if elem.text and elem.text.strip():
                    texts.append(elem.text.strip())
            if texts:
                blocks.append(" ".join(texts))
    return blocks

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/upload", methods=["GET","POST"])
def upload():
    if request.method == "POST":
        file = request.files.get("idml_file")
        if not file:
            return "No file selected"
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)
        session["idml_file"] = path
        return redirect(url_for("generate"))
    return render_template("upload_idml.html")

@app.route("/generate")
def generate():
    path = session.get("idml_file")
    if not path:
        return redirect(url_for("upload"))
    with zipfile.ZipFile(path, "r") as z:
        blocks = extract_story_blocks(z)
        dynamic_css = parse_styles(z)

    html = []
    for i, block in enumerate(blocks):
        cls = "body"
        if i == 0: cls = "title"
        elif i == 1: cls = "authors"
        html.append(f'<div class="{cls}">{block}</div>')

    return render_template("article.html", content="\n".join(html), dynamic_css=dynamic_css)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
