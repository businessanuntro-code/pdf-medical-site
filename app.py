from flask import Flask, render_template, request
import os, zipfile
from lxml import etree as ET
import traceback

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================
# EXTRACT IDML XML SAFE
# =========================
def read_xml(z, path):
    try:
        return ET.fromstring(z.read(path))
    except:
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

        # Text Frames (layout boxes)
        for node in root.iter():

            tag = node.tag.lower()

            # TEXT FRAME (IMPORTANT)
            if "textframe" in tag:

                geom = node.attrib.get("GeometricBounds", None)

                if geom:
                    try:
                        y1, x1, y2, x2 = map(float, geom.split(","))

                        frames.append({
                            "type": "frame",
                            "x": x1,
                            "y": y1,
                            "w": x2 - x1,
                            "h": y2 - y1,
                            "content": ""
                        })
                    except:
                        pass

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

                txt = " ".join(parts)

                if txt:
                    texts.append(txt)

    return texts


# =========================
# COMBINE STORY + FRAMES
# =========================
def combine(frames, texts):
    html = []

    for i, frame in enumerate(frames):

        content = texts[i] if i < len(texts) else ""

        html.append(f"""
        <div class="frame"
             style="
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
# UPLOAD + RENDER
# =========================
@app.route("/upload", methods=["GET", "POST"])
def upload():

    try:
        if request.method == "POST":

            file = request.files["idml_file"]

            path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(path)

            with zipfile.ZipFile(path, "r") as z:

                frames = parse_spreads(z)
                texts = parse_stories(z)

                html = combine(frames, texts)

            return render_template("article.html", content=html)

        return """
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="idml_file">
            <button type="submit">Upload IDML</button>
        </form>
        """

    except Exception:
        print(traceback.format_exc())
        return "ERROR - check logs"


if __name__ == "__main__":
    app.run(debug=True)
