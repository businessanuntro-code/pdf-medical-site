from flask import Flask, request, render_template, redirect, url_for
import fitz
import sqlite3
import json
import os
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------- DB --------------------
def init_db():
    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS articole (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titlu TEXT,
        slug TEXT,
        continut_html TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reguli TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -------------------- PDF BLOCKS --------------------
def extract_blocks(file_stream):
    doc = fitz.open(stream=file_stream.read(), filetype="pdf")
    page = doc[0]

    blocks = []
    raw_blocks = page.get_text("dict")["blocks"]

    for b in raw_blocks:
        if "lines" not in b:
            continue

        text = ""
        size = 0

        for line in b["lines"]:
            for span in line["spans"]:
                text += span["text"] + " "
                size = span["size"]

        text = text.strip()

        if text:
            blocks.append({
                "text": text,
                "size": size,
                "x": b["bbox"][0],
                "y": b["bbox"][1]
            })

    return blocks

# -------------------- APPLY TEMPLATE --------------------
def apply_template(blocks, template):
    html = ""

    for b in blocks:
        role = template.get(str(b["id"]))

        if role == "ignore":
            continue

        if role == "title_ro":
            html += f"<h1>{b['text']}</h1>"

        elif role == "abstract_title":
            html += f"<h2>{b['text']}</h2>"

        elif role == "abstract_text":
            html += f"<p>{b['text']}</p>"

        elif role == "title_en":
            html += f"<p><em>{b['text']}</em></p>"

        elif role == "section":
            html += f"<h2>{b['text']}</h2>"

        else:
            html += f"<p>{b['text']}</p>"

    return html

# -------------------- ROUTES --------------------

@app.route("/")
def home():
    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()
    cur.execute("SELECT titlu, slug FROM articole")
    articole = cur.fetchall()
    conn.close()

    return render_template("home.html", articole=articole)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files["pdf"]

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        with open(filepath, "rb") as f:
            blocks = extract_blocks(f)

        # atașăm ID pentru UI
        for i, b in enumerate(blocks):
            b["id"] = i

        # salvăm temporar
        with open("last_blocks.json", "w") as f:
            json.dump(blocks, f)

        return render_template("calibrate.html", blocks=blocks)

    return render_template("upload.html")


@app.route("/save_template", methods=["POST"])
def save_template():
    selections = request.form.to_dict()

    template = {}

    for key, value in selections.items():
        template[key] = value

    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute("DELETE FROM templates")  # păstrăm doar unul
    cur.execute("INSERT INTO templates (reguli) VALUES (?)", (json.dumps(template),))

    conn.commit()
    conn.close()

    return redirect("/generate")


@app.route("/generate")
def generate():
    with open("last_blocks.json") as f:
        blocks = json.load(f)

    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()
    cur.execute("SELECT reguli FROM templates ORDER BY id DESC LIMIT 1")
    template = json.loads(cur.fetchone()[0])
    conn.close()

    html = apply_template(blocks, template)

    titlu = "articol"
    slug = str(int(datetime.now().timestamp()))

    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO articole (titlu, slug, continut_html) VALUES (?, ?, ?)",
        (titlu, slug, html)
    )

    conn.commit()
    conn.close()

    return redirect(f"/articol/{slug}")


@app.route("/articol/<slug>")
def articol(slug):
    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute("SELECT continut_html FROM articole WHERE slug=?", (slug,))
    articol = cur.fetchone()

    conn.close()

    return render_template("article.html", content=articol[0])


# -------------------- RUN --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
