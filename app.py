from flask import Flask, render_template, request
import os
import zipfile
from lxml import etree as ET
import traceback

app = Flask(__name__)

# =========================
# SETUP
# =========================
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================
# SAFE XML PARSER
# =========================
def safe_xml(data):
    try:
        return ET.fromstring(data)
    except:
        return None


# =========================
# EXTRACT BOUNDS (ULTRA ROBUST)
# =========================
def extract_bounds(node):
    """
    Caută GeometricBounds oriunde în IDML
    """

    # 1. direct attributes
    if hasattr(node, "attrib"):
        for k, v in node.attrib.items():
            if "bounds" in k.lower():
                return v

    # 2. recursive search
    for child in node.iter():

        # attribute fallback
        if hasattr(child, "attrib"):
            for k, v in child.attrib.items():
                if "bounds" in k.lower():
                    return v

        # XML text fallback
        if child.text and isinstance(child.text, str):
            txt = child.text.strip()
            if txt.count(",") == 3:
                return txt

    return None


# =========================
# PARSE ALL LAYOUT AREAS
# =========================
def parse_layout(zip_file):
    frames = []

    for file in zip_file.namelist():

        # 🔥 SCAN EVERYTHING (Spreads + Master + even weird exports)
        if not any(x in file for x in ["Spreads", "Master", "Stories"]):
            continue

        xml = safe_xml(zip_file.read(file))
        if xml is None:
            continue

        for node in xml.iter():

            bounds = extract_bounds(node)

            if bounds:

                try:
                    parts = bounds.split(",")

                    if len(parts) != 4:
                        continue

                    y1, x1, y2, x2 = map(float, parts)

                    # ignore invalid boxes
                    if abs(x2 - x1) < 2 or abs(y2 - y1) < 2:
                        continue

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
# PARSE STORIES (TEXT SAFE)
# =========================
def parse_text(zip_file):
    texts = []

    for file in zip_file.namelist():

        if not file.startswith("Stories/"):
            continue

        xml = safe_xml(zip_file.read(file))
        if xml is None:
            continue

        buffer = []

        for node in xml.iter():

            if node.text and node.text.strip():
                txt = node.text.strip()

                if len(txt) > 1:
                    buffer.append(txt)

        if buffer:
            texts.append(" ".join(buffer))

    return texts


# =========================
# RENDER ENGINE
# =========================
def render(frames, texts):

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
                overflow:hidden;
                font-family:Times New Roman;
                font-size:12px;
                line-height:1.4;
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
    <h1>V7 IDML Medical Renderer</h1>
    <a href="/upload">Upload IDML</a>
    """


# =========================
# UPLOAD + PROCESS
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

                frames = parse_layout(z)
                texts = parse_text(z)

                # 🔥 IMPORTANT fallback
                if len(frames) == 0:
                    return "ERROR: No layout frames detected in IDML (file may be text-only export)"

                html = render(frames, texts)

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
        return "SERVER ERROR - check logs"


if __name__ == "__main__":
    app.run(debug=True)
