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
# EXTRACT STORIES (WITH IDS)
# =========================
def extract_stories(z):
    stories = {}

    for f in z.namelist():
        if not f.startswith("Stories/"):
            continue

        root = safe(z.read(f))
        if root is None:
            continue

        story_id = f

        paragraphs = []

        for node in root.iter():

            if node.text and node.text.strip():
                txt = node.text.strip()
                if len(txt) > 1:
                    paragraphs.append(txt)

        if paragraphs:
            stories[story_id] = paragraphs

    return stories


# =========================
# EXTRACT TABLES (basic IDML structure)
# =========================
def extract_tables(z):
    tables = []

    for f in z.namelist():
        if "Story" not in f:
            continue

        root = safe(z.read(f))
        if root is None:
            continue

        for table in root.iter():

            if "Table" in table.tag:

                rows = []

                for row in table.iter():

                    if "Row" in row.tag:
                        cells = []

                        for cell in row.iter():

                            if "Cell" in cell.tag:

                                text = ""

                                for t in cell.iter():
                                    if t.text:
                                        text += t.text.strip() + " "

                                cells.append(text.strip())

                        if cells:
                            rows.append(cells)

                if rows:
                    tables.append(rows)

    return tables


# =========================
# EXTRACT IMAGES
# =========================
def extract_images(z):
    images = []

    for f in z.namelist():
        if f.lower().endswith((".jpg", ".jpeg", ".png")):
            images.append(f)

    return images


# =========================
# EXTRACT THREADING (NEXT FRAME LOGIC)
# =========================
def extract_threading(z):
    links = {}

    for f in z.namelist():
        if not f.startswith("Spreads/"):
            continue

        root = safe(z.read(f))
        if root is None:
            continue

        for node in root.iter():

            nid = node.attrib.get("Self") or node.attrib.get("id")

            next_frame = node.attrib.get("NextTextFrame")
            prev_frame = node.attrib.get("PreviousTextFrame")

            if nid:
                links[nid] = {
                    "next": next_frame,
                    "prev": prev_frame
                }

    return links


# =========================
# EXTRACT FRAMES WITH POSITION
# =========================
def extract_frames(z):
    frames = {}

    for f in z.namelist():
        if not f.startswith("Spreads/"):
            continue

        root = safe(z.read(f))
        if root is None:
            continue

        for node in root.iter():

            tag = node.tag.lower()

            if "textframe" in tag or "rectangle" in tag:

                gb = None

                for k, v in node.attrib.items():
                    if "geometricbounds" in k.lower():
                        gb = v

                if not gb:
                    continue

                try:
                    y1, x1, y2, x2 = map(float, gb.split(","))

                    fid = node.attrib.get("Self") or str(len(frames))

                    frames[fid] = {
                        "x": x1,
                        "y": y1,
                        "w": x2 - x1,
                        "h": y2 - y1
                    }

                except:
                    continue

    return frames


# =========================
# BUILD THREAD ORDER
# =========================
def build_flow(threading_map):

    visited = set()
    ordered = []

    for k in threading_map.keys():

        if k in visited:
            continue

        current = k

        while current and current not in visited:
            ordered.append(current)
            visited.add(current)

            nxt = threading_map.get(current, {}).get("next")
            current = nxt

    return ordered


# =========================
# RENDER ENGINE
# =========================
def render(frames, stories, tables, images, flow):

    html = []
    story_list = list(stories.values())

    story_i = 0
    img_i = 0
    table_i = 0

    for i, frame_id in enumerate(flow):

        frame = frames.get(frame_id, None)
        if not frame:
            continue

        content = ""

        # =====================
        # TABLE PRIORITY
        # =====================
        if table_i < len(tables) and i % 6 == 0:
            table = tables[table_i]
            table_i += 1

            t_html = "<table border='1' style='width:100%;border-collapse:collapse'>"

            for row in table:
                t_html += "<tr>"
                for c in row:
                    t_html += f"<td>{c}</td>"
                t_html += "</tr>"

            t_html += "</table>"

            content += t_html

        # =====================
        # STORY FLOW
        # =====================
        if story_i < len(story_list):
            content += "<p>" + " ".join(story_list[story_i]) + "</p>"
            story_i += 1

        # =====================
        # IMAGES
        # =====================
        if img_i < len(images) and i % 4 == 0:
            content += f"<img src='/static/{images[img_i]}' style='max-width:100%'>"
            img_i += 1

        html.append(f"""
        <div style="
            position:absolute;
            left:{frame['x']}px;
            top:{frame['y']}px;
            width:{frame['w']}px;
            height:{frame['h']}px;
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
# HOME
# =========================
@app.route("/")
def home():
    return "<h1>V9 True InDesign Engine</h1><a href='/upload'>Upload IDML</a>"


# =========================
# UPLOAD
# =========================
@app.route("/upload", methods=["GET","POST"])
def upload():

    try:
        if request.method == "POST":

            file = request.files["idml_file"]
            path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(path)

            with zipfile.ZipFile(path, "r") as z:

                stories = extract_stories(z)
                tables = extract_tables(z)
                images = extract_images(z)
                frames = extract_frames(z)
                threading = extract_threading(z)

                flow = build_flow(threading)

                if not frames:
                    return "ERROR: No frames detected in IDML"

                html = render(frames, stories, tables, images, flow)

            return render_template("article.html", content=html)

        return """
        <form method='POST' enctype='multipart/form-data'>
            <input type='file' name='idml_file'>
            <button>Upload IDML</button>
        </form>
        """

    except:
        print(traceback.format_exc())
        return "SERVER ERROR"


if __name__ == "__main__":
    app.run(debug=True)
