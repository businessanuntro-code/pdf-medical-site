from flask import Flask, request, render_template, redirect
import fitz  # PyMuPDF
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
        continut_json TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- PDF ----------------
def extract_medical_article(file_stream):
    doc = fitz.open(stream=file_stream.read(), filetype="pdf")
    result = {
        "title_ro": "",
        "title_en": "",
        "authors": "",
        "abstract": "",
        "keywords": "",
        "rezumat": "",
        "cuvinte_cheie": "",
        "body": "",
        "bibliografie": ""
    }

    # Patterns pentru secțiuni
    import re
    patterns = {
        "abstract": re.compile(r"\babstract\b", re.IGNORECASE),
        "keywords": re.compile(r"\bkeywords\b", re.IGNORECASE),
        "rezumat": re.compile(r"\brezumat\b", re.IGNORECASE),
        "cuvinte_cheie": re.compile(r"\bcuvinte[- ]cheie\b", re.IGNORECASE),
        "bibliografie": re.compile(r"\b(bibliografie|references|literatura)\b", re.IGNORECASE)
    }

    full_text = ""
    for page in doc:
        full_text += page.get_text("text") + "\n"

    lines = full_text.split("\n")
    current_section = "body"  # Default section

    for i, line in enumerate(lines):
        line_clean = line.strip()
        if not line_clean:
            continue

        # Primele 3 linii: Titlu RO, Titlu EN, Autori
        if i == 0:
            result["title_ro"] = line_clean
            continue
        elif i == 1:
            result["title_en"] = line_clean
            continue
        elif i == 2:
            result["authors"] = line_clean
            continue

        # Detectare secțiune după pattern
        matched = False
        for key, pat in patterns.items():
            if pat.search(line_clean):
                current_section = key
                matched = True
                break
        if matched:
            continue

        # Adaugă linia în secțiunea curentă
        if current_section in result:
            result[current_section] += line_clean + " "

    # Salvează tot conținutul complet
    result["body"] = full_text

    return result

# ---------------- ROUTES ----------------
@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files["pdf_file"]
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        with open(path, "rb") as f:
            article_data = extract_medical_article(f)

        # Salvează în DB
        slug = str(int(datetime.now().timestamp()))
        conn = sqlite3.connect("db.sqlite")
        cur = conn.cursor()
        cur.execute("INSERT INTO articole (slug, continut_json) VALUES (?,?)",
                    (slug, json.dumps(article_data)))
        conn.commit()
        conn.close()

        # Redirect către Builder cu datele prepopulate
        return render_template("builder.html", blocks=[article_data])

    return render_template("upload.html")

@app.route("/view/<slug>")
def view(slug):
    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()
    cur.execute("SELECT continut_json FROM articole WHERE slug=?", (slug,))
    row = cur.fetchone()
    conn.close()
    if row:
        content = json.loads(row[0])
        return render_template("article.html", content=content)
    return "Articolul nu a fost găsit", 404

@app.route("/articles")
def articles():
    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()
    cur.execute("SELECT slug, json_extract(continut_json, '$.title_ro') FROM articole ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return render_template("articles.html", articles=rows)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
