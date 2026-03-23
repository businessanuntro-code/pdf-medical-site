from flask import Flask, request, render_template, redirect, url_for
import fitz  # PyMuPDF
import sqlite3
import re
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
        slug TEXT UNIQUE,
        continut_html TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -------------------- UTILS --------------------
def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')[:80]

def extract_first_page_html(file_stream):
    doc = fitz.open(stream=file_stream.read(), filetype="pdf")
    page = doc[0]

    blocks = page.get_text("dict")["blocks"]

    html = ""
    title = None

    for block in blocks:
        if "lines" not in block:
            continue

        text = ""
        size = 0

        for line in block["lines"]:
            for span in line["spans"]:
                text += span["text"] + " "
                size = span["size"]

        text = text.strip()
        if not text:
            continue

        if size > 14 and not title:
            title = text
            html += f"<h1>{text}</h1>"
        elif "abstract" in text.lower():
            html += f"<h2>{text}</h2>"
        elif size > 11:
            html += f"<h3>{text}</h3>"
        else:
            html += f"<p>{text}</p>"

    if not title:
        title = "articol-fara-titlu"

    return title, html

# -------------------- ROUTES --------------------
@app.route("/", methods=["GET"])
def home():
    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute("SELECT titlu, slug FROM articole ORDER BY id DESC")
    articole = cur.fetchall()

    conn.close()

    return render_template("home.html", articole=articole)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files["pdf"]

        if file:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)

            with open(filepath, "rb") as f:
                titlu, html = extract_first_page_html(f)

            slug = slugify(titlu)

            conn = sqlite3.connect("db.sqlite")
            cur = conn.cursor()

            cur.execute(
                "INSERT OR IGNORE INTO articole (titlu, slug, continut_html, created_at) VALUES (?, ?, ?, ?)",
                (titlu, slug, html, datetime.now().isoformat())
            )

            conn.commit()
            conn.close()

            return redirect(url_for('articol', slug=slug))

    return render_template("upload.html")

@app.route("/articol/<slug>")
def articol(slug):
    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute("SELECT titlu, continut_html FROM articole WHERE slug=?", (slug,))
    articol = cur.fetchone()

    conn.close()

    if not articol:
        return "Articol inexistent"

    # Trimitem continutul articolului către template-ul nostru article.html
    # Putem adăuga secțiuni suplimentare dacă vrei mai târziu
    article_data = {
        "title": articol[0],
        "intro": "",
        "sections": [
            {
                "subtitle": "",
                "paragraphs": [articol[1]],
                "list_items": None
            }
        ]
    }

    return render_template("article.html", article=article_data)

# -------------------- RUN --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
