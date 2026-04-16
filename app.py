from flask import Flask, render_template, request
import os
import zipfile
from lxml import etree as ET
import traceback

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================
# SAFE XML
# =========================
def xml_safe(data):
    try:
        return ET.fromstring(data)
    except:
        return None


# =========================
# EXTRACT STORY TEXT ORDERED
# =========================
def extract_stories(z):
    stories = []

    for file in z.namelist():
        if not file.startswith("Stories/"):
            continue

        xml = xml_safe(z.read(file))
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
# EXTRACT IMAGES (PLACEHOLDERS)
# =========================
def extract_images(z):
    images = []

    for file in z.namelist():
        if "Resources" in file and file.endswith((".jpg", ".png", ".jpeg")):
            images.append(file)

    return images


# =========================
# EXTRACT LAYOUT FRAMES (FULL SCAN)
# =========================
def extract_frames(z):
    frames = []

    for file in z.namelist():
        if not any(x in file for x in ["Spreads", "Master", "Stories"]):
            continue

        xml = xml_safe(z.read(file))
        if xml is None:
            continue

        for node in xml.iter():

            bounds = None

            # attribute bounds
            if hasattr(node, "attrib"):
                for k, v in node.attrib.items():
                    if "bounds" in k.lower():
                        bounds = v

            # nested bounds
            for child in node.iter():
                if child.text and isinstance(child.text, str):
                    if child.text.count(",") == 3:
                        bounds = child.text.strip()

            if bounds:
                try:
                    y1, x1, y2, x2 = map(float, bounds.split(","))

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
# JOURNAL RENDER ENGINE
# =========================
def render(frames, stories, images):

    html = []
    img_index = 0
    story_index = 0

    for i, frame in enumerate(frames):

        content = ""

        # decide content type
        if story_index < len(stories):
            content = " ".join(stories[story_index])
            story_index += 1

        # inject image if available
        if img_index < len(images) and i % 5 == 0:
            img = images[img_index]
            content += f'<br><img src="/static/{img}" style="max-width:100%;">'
            img_index += 1

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
    return """
    <h1>V8 Full Journal Replica Engine</h1>
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

                if not frames:
                    return "ERROR: No layout frames found"

                html = render(frames, stories, images)

            return render_template("article.html", content=html)

        return """
        <h2>Upload IDML (V8)</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="idml_file">
            <button>Render Journal</button>
        </form>
        """

    except Exception:
        print(traceback.format_exc())
        return "SERVER ERROR"


if __name__ == "__main__":
    app.run(debug=True)
