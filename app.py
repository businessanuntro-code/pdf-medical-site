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
def safe_parse(xml_bytes):
    try:
        return ET.fromstring(xml_bytes)
    except:
        return None


# =========================
# EXTRACT GEOMETRIC BOUNDS (RECURSIVE)
# =========================
def find_bounds(node):
    """
    Caută GeometricBounds oriunde în XML node (IDML safe)
    """
    for child in node.iter():

        tag = child.tag.lower() if isinstance(child.tag, str) else ""

        if "geometricbounds" in tag:
            if child.text:
                return child.text

    return None


# =========================
# PARSE SPREADS → FRAMES
# =========================
def parse_spreads(z):
    frames = []

    for file in z.namelist():

        if "Spreads" not in file:
            continue

        xml = safe_parse(z.read(file))
        if xml is None:
            continue

        for node in xml.iter():

            # accept ANY object that might contain layout
            tag = str(node.tag).lower()

            if any(x in tag for x in ["textframe", "pageitem", "rectangle", "oval"]):

                bounds = find_bounds(node)

                if not bounds:
                    bounds = node.attrib.get("GeometricBounds")

                if bounds:
                    try:
                        y1, x1, y2, x2 = map(float, bounds.split(","))

                        if x2 > x1 and y2 > y1:

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
# PARSE STORIES → TEXT BLOCKS
# =========================
def parse_stories(z):
    texts = []

    for file in z.namelist():

        if not file.startswith("Stories/"):
            continue

        xml = safe_parse(z.read(file))
        if xml is None:
            continue

        buffer = []

        for node in xml.iter():

            if node.text and node.text.strip():

                txt = node.text.strip()

                # filtrare zgomot XML
                if len(txt) > 1:
                    buffer.append(txt)

        if buffer:
            texts.append(" ".join(buffer))

    return texts


# =========================
# COMBINE LAYOUT + TEXT
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
    <h1>V6 IDML Medical Journal Engine</h1>
    <p>Pixel layout reconstruction (stable version)</p>
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

                # fallback safety
                if not frames:
                    return "ERROR: No frames detected in Spreads"

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
        return "SERVER ERROR (check logs)"


if __name__ == "__main__":
    app.run(debug=True)
