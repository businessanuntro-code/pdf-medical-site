from flask import Flask, request, render_template_string, redirect, url_for
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

# 🔥 PARSER AVANSAT CU STRUCTURĂ + PARAGRAFE
def extract_first_page_html(file_stream):
    doc = fitz.open(stream=file_stream.read(), filetype="pdf")
    page = doc[0]

    blocks = page.get_text("dict")["blocks"]

    data = {
        "title_ro": "",
        "title_en": "",
        "authors": "",
        "abstract": {"text": "", "keywords": ""},
        "rezumat": {"text": "", "keywords": ""},
        "content": []
    }

    current_section = None
    last_y = None

    for block in blocks:
        if "lines" not in block:
            continue

        x0, y0, x1, y1 = block["bbox"]

        # ❌ ignoră header reviste
        if y0 < 80:
            continue

        lines_text = []
        size = 0

        for line in block["lines"]:
            line_text = ""
            for span in line["spans"]:
                line_text += span["text"]
                size = span["size"]

            lines_text.append(line_text.strip())

        text = " ".join(lines_text).strip()

        if not text:
            continue

        # ❌ elimină junk
        if any(x in text.lower() for x in [
            "issn", "submission date", "acceptance date", "orl.ro"
        ]):
            continue

        # ❌ elimină numere simple
        if re.fullmatch(r"\d+", text):
            continue

        # ---------------- TITLU RO ----------------
        if not data["title_ro"] and size > 16:
            data["title_ro"] = text
            continue

        # ---------------- ABSTRACT ----------------
        if "abstract" in text.lower():
            current_section = "abstract"
            continue

        if current_section == "abstract":
            if "cuvinte-cheie" in text.lower() or "keywords" in text.lower():
                data["abstract"]["keywords"] = text
            else:
                data["abstract"]["text"] += text + "\n\n"
            continue

        # ---------------- REZUMAT ----------------
        if "rezumat" in text.lower():
            current_section = "rezumat"
            continue

        if current_section == "rezumat":
            if "cuvinte-cheie" in text.lower():
                data["rezumat"]["keywords"] = text
            else:
                data["rezumat"]["text"] += text + "\n\n"
            continue

        # ---------------- TITLU EN ----------------
        if data["abstract"]["text"] and not data["title_en"] and size > 11:
            data["title_en"] = text
            continue

        # ---------------- INTRODUCERE ----------------
        if "introducere" in text.lower():
            current_section = "content"
            data["content"].append({"type": "h2", "text": text})
            continue

        # ---------------- CONTENT ----------------
        if current_section == "content":
            # separare paragraf după distanță verticală
            if last_y and abs(y0 - last_y) > 25:
                data["content"].append({"type": "p", "text": ""})

            if size > 12:
                data["content"].append({"type": "h3", "text": text})
            else:
                data["content"].append({"type": "p", "text": text})

        last_y = y0

    if not data["title_ro"]:
        data["title_ro"] = "articol-fara-titlu"

    # ---------------- HTML FINAL ----------------
    html = ""

    html += f"<h1>{data['title_ro']}</h1>"

    if data["title_en"]:
        html += f"<p><em>{data['title_en']}</em></p>"

    html += "<h2>Abstract</h2>"
    html += f"<p>{data['abstract']['text'].replace(chr(10), '<br><br>')}</p>"

    if data["abstract"]["keywords"]:
        html += f"<p><strong>{data['abstract']['keywords']}</strong></p>"

    html += "<h2>Rezumat</h2>"
    html += f"<p>{data['rezumat']['text'].replace(chr(10), '<br><br>')}</p>"

    if data["rezumat"]["keywords"]:
        html += f"<p><strong>{data['rezumat']['keywords']}</strong></p>"

    for block in data["content"]:
        if block["type"] == "h2":
            html += f"<h2>{block['text']}</h2>"
        elif block["type"] == "h3":
            html += f"<h3>{block['text']}</h3>"
        else:
            if block["text"]:
                html += f"<p>{block['text']}</p>"

    return data["title_ro"], html

# -------------------- ROUTES --------------------
@app.route("/", methods=["GET"])
def home():
    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute("SELECT titlu, slug FROM articole ORDER BY id DESC")
    articole = cur.fetchall()

    conn.close()

    return render_template_string("""
    <h1>Articole Medicale</h1>

    <a href='/upload'>+ Upload articol nou</a>

    <ul>
    {% for a in articole %}
        <li>
            <a href="/articol/{{a[1]}}">{{a[0]}}</a>
        </li>
    {% endfor %}
    </ul>
    """, articole=articole)

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

    return render_template_string("""
    <h1>Upload PDF</h1>

    <form method="post" enctype="multipart/form-data">
        <input type="file" name="pdf">
        <button type="submit">Upload</button>
    </form>

    <br>
    <a href="/">Înapoi</a>
    """)

@app.route("/articol/<slug>")
def articol(slug):
    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute("SELECT titlu, continut_html FROM articole WHERE slug=?", (slug,))
    articol = cur.fetchone()

    conn.close()

    if not articol:
        return "Articol inexistent"

    return render_template_string("""
    <a href="/">← Înapoi</a>
    <h1>{{articol[0]}}</h1>
    <div>
        {{articol[1] | safe}}
    </div>
    """, articol=articol)

# -------------------- RUN --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
