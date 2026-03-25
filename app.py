from flask import Flask, request, render_template, redirect
import fitz
import sqlite3
import json
import os
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DB ----------------
def init_db():
    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS articole (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT,
        continut_html TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        structura TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- PDF ----------------
def extract_blocks(file_stream):
    doc = fitz.open(stream=file_stream.read(), filetype="pdf")
    page = doc[0]

    blocks = []
    raw = page.get_text("dict")["blocks"]

    for b in raw:
        if "lines" not in b:
            continue

        text = ""
        for line in b["lines"]:
            for span in line["spans"]:
                text += span["text"] + " "

        text = text.strip()

        if text:
            blocks.append({
                "id": len(blocks),
                "text": text
            })

    return blocks

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files["pdf_file"]
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        with open(path, "rb") as f:
            blocks = extract_blocks(f)

        # Preluam structura salvata anterior
        conn = sqlite3.connect("db.sqlite")
        cur = conn.cursor()
        cur.execute("SELECT structura FROM templates ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        template_data = json.loads(row[0]) if row else None
        conn.close()

        if template_data:
            # Folosim șablonul salvat pentru a prepopula builder-ul
            for i in range(len(blocks)):
                if i < len(template_data):
                    blocks[i]['text'] = template_data[i]['html']

        return render_template("builder.html", blocks=blocks)

    return render_template("upload.html")

@app.route("/save", methods=["POST"])
def save():
    data = json.loads(request.form["data"])

    html = ""
    for b in data:
        html += f"<div>{b['html']}</div>"

    slug = str(int(datetime.now().timestamp()))

    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute("INSERT INTO articole (slug, continut_html) VALUES (?,?)", (slug, html))
    cur.execute("DELETE FROM templates")
    cur.execute("INSERT INTO templates (structura) VALUES (?)", (json.dumps(data),))

    conn.commit()
    conn.close()

    return redirect(f"/view/{slug}")

@app.route("/view/<slug>")
def view(slug):
    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute("SELECT continut_html FROM articole WHERE slug=?", (slug,))
    html = cur.fetchone()[0]

    conn.close()

    return f"<div style='max-width:800px;margin:auto'>{html}</div>"

@app.route("/articles")
def articles_list():
    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()
    cur.execute("SELECT id, slug FROM articole ORDER BY id DESC")
    articles = cur.fetchall()
    conn.close()
    return render_template("articles.html", articles=articles)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
