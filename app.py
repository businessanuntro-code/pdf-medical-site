from flask import Flask, render_template, request
import os
import zipfile
from lxml import etree as ET
import traceback

app = Flask(__name__)

# -------------------------
# SETUP
# -------------------------
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================
# SAFE XML READER
# =========================
def read_xml(z, path):
    try:
        data = z.read(path)
        return ET.fromstring(data)
    except Exception:
        return None


# =========================
# PARSE SPREADS (LAYOUT)
# =========================
def parse_spreads(z):
    frames = []

    spread_files = [f for f in z.namelist() if f.startswith("Spreads/")]

    for file in spread_files:
        root = read_xml(z, file)
        if root is None:
            continue

        for node in root.iter():

            tag = node.tag.lower()

            # TEXT FRAME (layout box)
            if "textframe" in tag:

                geom = node.attrib.get("GeometricBounds", None)

                if geom:
                    try:
                        y1, x1, y2, x2 = map(float, geom.split(","))

                        frames.append({
                            "x": x1,
                            "y": y1,
                            "w": x2 - x1,
                            "h": y2 - y1
                        })
                    except:
                        continue

    return frames


# =========================
# PARSE STORIES (TEXT)
# =========================
def parse_stories(z):
    texts = []

    story_files = [f for f in z.namelist() if f.startswith("Stories/")]

    for file in story_files:
        root = read_xml(z, file)
        if root is None:
            continue

        for node in root.iter():

            if "ParagraphStyleRange" in node.tag:

                parts = []

                for t in node.iter():
                    if t.text and t.text.strip():
                        parts.append(t.text.strip())

                text = " ".join(parts).strip()

                if text:
                    texts.append(text)

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
# HOME PAGE
# =========================
@app.route("/")
def home():
    return """
    <h1>Medical Journal IDML Engine V5</h1>
    <p>InDesign-like renderer (Spreads + Frames)</p>
    <a href="/upload">Go to Upload</a>
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

                html = combine(frames, texts)

            return render_template("article.html", content=html)

        return """
        <h2>Upload IDML File</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="idml_file" accept=".idml">
            <button type="submit">Render Journal</button>
        </form>
        """

    except Exception:
        print(traceback.format_exc())
        return "SERVER ERROR - check logs"


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
