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
    title_ro = None
    title_en = None
    seen_abstract = False
    seen_intro = False

    page_width = page.rect.width

    for block in blocks:
        if "lines" not in block:
            continue

        x0, y0, x1, y1 = block["bbox"]

        # ❌ IGNORĂ HEADER (sus)
        if y0 < 80:
            continue

        # ❌ IGNORĂ COLOANA STÂNGA (autori)
        if x0 < page_width * 0.2:
            continue

        text = ""
        size = 0
        is_bold = False
        is_italic = False
        is_sup = False

        for line in block["lines"]:
            for span in line["spans"]:
                t = span["text"]

                font = span.get("font", "").lower()

                if "bold" in font:
                    is_bold = True
                if "italic" in font or "oblique" in font:
                    is_italic = True

                if span.get("flags", 0) & 1:
                    is_sup = True

                size = span["size"]
                text += t + " "

        text = text.strip()

        # ❌ elimină numere izolate
        if re.fullmatch(r"\d+", text):
            continue

        if not text:
            continue

        # -------------------------
        # 1️⃣ TITLU ROMÂNĂ
        # -------------------------
        if not title_ro and size > 16:
            title_ro = text
            html += f"<h1 style='text-align:left'>{text}</h1>"
            continue

        # -------------------------
        # 2️⃣ ABSTRACT / REZUMAT
        # -------------------------
        if "abstract" in text.lower() or "rezumat" in text.lower():
            seen_abstract = True
            html += f"<h2 style='text-align:left'>{text}</h2>"
            continue

        if seen_abstract and not title_en:
            html += f"<p style='text-align:left'>{text}</p>"
            continue

        # -------------------------
        # 3️⃣ TITLU ENGLEZĂ (italic)
        # -------------------------
        if seen_abstract and not title_en and size > 11:
            title_en = text
            html += f"<p style='text-align:left'><em>{text}</em></p>"
            continue

        # -------------------------
        # 4️⃣ INTRODUCERE
        # -------------------------
        if "introducere" in text.lower():
            seen_intro = True
            html += f"<h2 style='text-align:left'>{text}</h2>"
            continue

        # -------------------------
        # 5️⃣ CONȚINUT
        # -------------------------
        formatted_text = text

        if is_bold:
            formatted_text = f"<strong>{formatted_text}</strong>"
        if is_italic:
            formatted_text = f"<em>{formatted_text}</em>"
        if is_sup:
            formatted_text = f"<sup>{formatted_text}</sup>"

        if size > 12:
            html += f"<h3 style='text-align:left'>{formatted_text}</h3>"
        else:
            html += f"<p style='text-align:left'>{formatted_text}</p>"

    if not title_ro:
        title_ro = "articol-fara-titlu"

    return title_ro, html

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
