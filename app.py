from flask import Flask, render_template, request
import os, zipfile
from lxml import etree as ET
import traceback

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================
# SAFE XML
# =========================
def safe(xml):
    try:
        return ET.fromstring(xml)
    except:
        return None


# =========================
# STORIES
# =========================
def extract_stories(z):
    stories = []

    for f in z.namelist():
        if not f.startswith("Stories/"):
            continue

        root = safe(z.read(f))
        if root is None:
            continue

        buffer = []

        for n in root.iter():
            if n.text and n.text.strip():
                buffer.append(n.text.strip())

        if buffer:
            stories.append(buffer)

    return stories


# =========================
# FRAMES (SAFE MODE)
# =========================
def extract_frames(z):
    frames = []

    for f in z.namelist():
        if "Spreads" not in f:
            continue

        root = safe(z.read(f))
        if root is None:
            continue

        for n in root.iter():

            tag = n.tag.lower()

            if "textframe" in tag or "rectangle" in tag:

                gb = None

                # geometric bounds safe search
                for k, v in n.attrib.items():
                    if "geometricbounds" in k.lower():
                        gb = v

                if not gb:
                    continue

                try:
                    y1, x1, y2, x2 = map(float, gb.split(","))

                    frames.append({
                        "x": x1,
                        "y": y1,
                        "w": max(10, x2 - x1),
                        "h": max(10, y2 - y1)
                    })

                except:
                    continue

    return frames


# =========================
# IMAGES
# =========================
def extract_images(z):
    return [
        f for f in z.namelist()
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]


# =========================
# SAFE RENDER (NO CRASH)
# =========================
def render(frames, stories, images):

    html = []

    story_i = 0
    img_i = 0

    if not frames:
        return "<h3>No frames found (fallback mode active)</h3>"

    for i, f in enumerate(frames):

        content = ""

        # story
        if story_i < len(stories):
            content += "<p>" + " ".join(stories[story_i]) + "</p>"
            story_i += 1

        # image
        if img_i < len(images) and i % 5 == 0:
            content += f"<img src='/static/{images[img_i]}' style='max-width:100%'>"
            img_i += 1

        html.append(f"""
        <div style="
            position:absolute;
            left:{f['x']}px;
            top:{f['y']}px;
            width:{f['w']}px;
            height:{f['h']}px;
            overflow:hidden;
            font-family:Times New Roman;
            font-size:12px;
            line-height:1.4;
            border:1px solid #eee;
            box-sizing:border-box;
            padding:4px;
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
    return "<h1>V9 SAFE ENGINE</h1><a href='/upload'>Upload IDML</a>"


# =========================
# UPLOAD (CRASH PROOF)
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

                html = render(frames, stories, images)

            return render_template("article.html", content=html)

        return """
        <h2>Upload IDML</h2>
        <form method='POST' enctype='multipart/form-data'>
            <input type='file' name='idml_file'>
            <button>Render</button>
        </form>
        """

    except Exception:
        print(traceback.format_exc())
        return "SERVER ERROR (check logs)"


if __name__ == "__main__":
    app.run(debug=True)
