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
def safe_xml(data):
    try:
        return ET.fromstring(data)
    except:
        return None


# =========================
# EXTRACT STORIES (fallback content)
# =========================
def extract_stories(z):
    stories = []

    for f in z.namelist():
        if not f.startswith("Stories/"):
            continue

        xml = safe_xml(z.read(f))
        if xml is None:
            continue

        buffer = []

        for node in xml.iter():
            if node.text and node.text.strip():
                txt = node.text.strip()
                if len(txt) > 1:
                    buffer.append(txt)

        if buffer:
            stories.append(buffer)

    return stories


# =========================
# EXTRACT IMAGES (optional)
# =========================
def extract_images(z):
    imgs = []

    for f in z.namelist():
        if f.lower().endswith((".jpg", ".png", ".jpeg")):
            imgs.append(f)

    return imgs


# =========================
# GET GEOMETRIC BOUNDS SAFE
# =========================
def get_bounds(node):
    for k, v in node.attrib.items():
        if "geometricbounds" in k.lower():
            return v

    for child in node:
        if child.text and "," in child.text:
            return child.text.strip()

    return None


# =========================
# EXTRACT LAYOUT FRAMES (FIXED V8)
# =========================
def extract_frames(z):
    frames = []

    for f in z.namelist():
        if not f.startswith("Spreads/"):
            continue

        xml = safe_xml(z.read(f))
        if xml is None:
            continue

        for node in xml.iter():

            tag = node.tag.lower()

            # accept ANY InDesign object type
            if any(x in tag for x in ["textframe", "rectangle", "pageitem", "graphic"]):

                bounds = get_bounds(node)

                if not bounds:
                    continue

                try:
                    parts = bounds.split(",")
                    if len(parts) != 4:
                        continue

                    y1, x1, y2, x2 = map(float, parts)

                    w = x2 - x1
                    h = y2 - y1

                    if w < 2 or h < 2:
                        continue

                    frames.append({
                        "x": x1,
                        "y": y1,
                        "w": w,
                        "h": h
                    })

                except:
                    continue

    return frames


# =========================
# SMART MODE DETECTOR
# =========================
def has_real_layout(frames):
    return len(frames) > 0


# =========================
# HTML RENDER ENGINE
# =========================
def render_layout(frames, stories, images):

    html = []
    story_i = 0
    img_i = 0

    for i, f in enumerate(frames):

        content = ""

        # story mapping
        if story_i < len(stories):
            content = " ".join(stories[story_i])
            story_i += 1

        # inject images occasionally
        if img_i < len(images) and i % 4 == 0:
            content += f"<br><img src='/static/{images[img_i]}' style='max-width:100%'>"
            img_i += 1

        html.append(f"""
        <div class="frame"
             style="
                position:absolute;
                left:{f['x']}px;
                top:{f['y']}px;
                width:{f['w']}px;
                height:{f['h']}px;
                overflow:hidden;
                font-family:Times New Roman;
                font-size:12px;
                line-height:1.4;
                padding:6px;
                box-sizing:border-box;
             ">
            {content}
        </div>
        """)

    return "\n".join(html)


# =========================
# FALLBACK MODE (NO LAYOUT)
# =========================
def render_structured(stories):

    html = ""

    for i, block in enumerate(stories):

        cls = "body"

        if i == 0:
            cls = "title"
        elif i == 1:
            cls = "authors"
        elif "abstract" in " ".join(block).lower():
            cls = "abstract"

        html += f"<div class='{cls}'>" + "<p>".join(block) + "</p></div>"

    return html


# =========================
# HOME
# =========================
@app.route("/")
def home():
    return """
    <h1>V8 IDML Journal Engine (FIXED)</h1>
    <a href="/upload">Upload IDML</a>
    """


# =========================
# UPLOAD
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

                frames = extract_frames(z)
                stories = extract_stories(z)
                images = extract_images(z)

                # =========================
                # MODE SWITCH
                # =========================
                if has_real_layout(frames):
                    html = render_layout(frames, stories, images)
                else:
                    html = render_structured(stories)

            return render_template("article.html", content=html)

        return """
        <h2>Upload IDML</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="idml_file">
            <button>Render</button>
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
