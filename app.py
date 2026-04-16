from flask import Flask, render_template, request
import os, zipfile
from lxml import etree as ET
import traceback

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def safe(xml_bytes):
    try:
        return ET.fromstring(xml_bytes)
    except:
        return None


# =========================
# DETECT TYPE OF IDML
# =========================
def detect_layout(zip_file):
    for f in zip_file.namelist():
        if "Spreads" in f:
            xml = safe(zip_file.read(f))
            if xml is None:
                continue

            for n in xml.iter():
                if "TextFrame" in n.tag:
                    return True
    return False


# =========================
# STRUCTURED MODE (SAFE FALLBACK)
# =========================
def extract_structured(zip_file):
    articles = []

    for f in zip_file.namelist():
        if not f.startswith("Stories/"):
            continue

        xml = safe(zip_file.read(f))
        if xml is None:
            continue

        buffer = []

        for n in xml.iter():
            if n.text and n.text.strip():
                txt = n.text.strip()
                if len(txt) > 1:
                    buffer.append(txt)

        if buffer:
            articles.append(buffer)

    return articles


# =========================
# SIMPLE LAYOUT MODE (IF EXISTS)
# =========================
def extract_layout(zip_file):
    frames = []

    for f in zip_file.namelist():
        if "Spreads" not in f:
            continue

        xml = safe(zip_file.read(f))
        if xml is None:
            continue

        for n in xml.iter():
            if hasattr(n, "attrib"):
                for k, v in n.attrib.items():
                    if "bounds" in k.lower():
                        try:
                            y1,x1,y2,x2 = map(float, v.split(","))
                            frames.append((x1,y1,x2,y2))
                        except:
                            pass

    return frames


# =========================
# HOME
# =========================
@app.route("/")
def home():
    return "<h1>IDML Engine Smart V8</h1><a href='/upload'>upload</a>"


# =========================
# UPLOAD
# =========================
@app.route("/upload", methods=["GET","POST"])
def upload():

    try:
        if request.method == "POST":

            file = request.files.get("idml_file")
            path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(path)

            with zipfile.ZipFile(path, "r") as z:

                has_layout = detect_layout(z)

                # =========================
                # MODE SWITCH
                # =========================
                if has_layout:

                    frames = extract_layout(z)

                    if not frames:
                        return "Layout detected but no frames parsed"

                    html = "".join([
                        f"<div style='position:absolute;left:{x}px;top:{y}px;width:{x2-x}px;height:{y2-y}px;border:1px solid black'>FRAME</div>"
                        for x,y,x2,y2 in frames
                    ])

                    return render_template("article.html", content=html)

                else:

                    # 🔵 STRUCTURED MODE
                    articles = extract_structured(z)

                    html = ""

                    for block in articles:
                        html += "<div class='article'>"
                        html += "<p>" + "</p><p>".join(block) + "</p>"
                        html += "</div>"

                    return render_template("article.html", content=html)

        return "<form method='post' enctype='multipart/form-data'><input type='file' name='idml_file'><button>upload</button></form>"

    except:
        print(traceback.format_exc())
        return "ERROR"


if __name__ == "__main__":
    app.run(debug=True)
