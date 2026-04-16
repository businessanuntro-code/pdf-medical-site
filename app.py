from flask import Flask, render_template, request
import os
import zipfile
from lxml import etree as ET
import traceback

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================
# SAFE XML PARSER
# =========================
def safe_xml(xml_bytes):
    try:
        return ET.fromstring(xml_bytes)
    except:
        return None


# =========================
# PARSE SPREADS (LAYOUT SAFE)
# =========================
def parse_spreads(zip_file):
    frames = []

    try:
        for file in zip_file.namelist():
            if "Spreads" not in file:
                continue

            xml = safe_xml(zip_file.read(file))
            if xml is None:
                continue

            for node in xml.iter():

                tag = node.tag.lower()

                if "textframe" in tag or "pageitem" in tag:

                    bounds = None

                    # caută GeometricBounds oriunde în sub-tree
                    for child in node.iter():
                        if "geometricbounds" in child.tag.lower():
                            bounds = child.text

                    if bounds:
                        try:
                            y1, x1, y2, x2 = map(float, bounds.split(","))

                            frames.append({
                                "x": x1,
                                "y": y1,
                                "w": x2 - x1,
                                "h": y2 - y1
                            })
                        except:
                            continue

    except Exception:
        print("SPREAD ERROR:", traceback.format_exc())

    return frames


# =========================
# PARSE STORIES (TEXT SAFE)
# =========================
def parse_stories(zip_file):
    texts = []

    try:
        for file in zip_file.namelist():
            if not file.startswith("Stories/"):
                continue

            xml = safe_xml(zip_file.read(file))
            if xml is None:
                continue

            for node in xml.iter():

                if "ParagraphStyleRange" in node.tag:

                    parts = []

                    for t in node.iter():
                        if t.text and t.text.strip():
                            parts.append(t.text.strip())

                    text = " ".join(parts).strip()

                    if text:
                        texts.append(text)

    except Exception:
        print("STORY ERROR:", traceback.format_exc())

    return texts


# =========================
# COMBINE LAYOUT + TEXT
# =========================
def combine(frames, texts):
    html = []

    for i, frame in enumerate(frames):

        content = texts[i] if i < len(texts) else ""

        html.append(f"""
        <div class="frame"
             style="
                position:absolute;
                left:{frame['x']}px;
                top:{frame['y']}px;
                width:{frame['w']}px;
                height:{frame['h']}px;
             ">
            {content}
        </div>
        """)

    return "\n".join(html)


# =========================
# HOME
# =========================
@app.route("/")
def home():
    return """
    <h1>V5 IDML Journal Engine</h1>
    <a href="/upload">Upload IDML</a>
    """


# =========================
# UPLOAD + RENDER
# =========================
@app.route("/upload", methods=["GET", "POST"])
def upload():

    try:
        if request.method == "POST":

            file = request.files.get("idml_file")
            if not file:
                return "No file uploaded"

            path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(path)

            with zipfile.ZipFile(path, "r") as z:

                frames = parse_spreads(z)
                texts = parse_stories(z)

                if not frames:
                    return "No frames found in IDML (Spreads issue)"

                html = combine(frames, texts)

            return render_template("article.html", content=html)

        return """
        <h2>Upload IDML</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="idml_file">
            <button type="submit">Render</button>
        </form>
        """

    except Exception:
        print(traceback.format_exc())
        return "SERVER ERROR (check logs)"


if __name__ == "__main__":
    app.run(debug=True)
