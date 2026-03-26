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

    patterns = {
        "abstract": ["abstract"],
        "keywords": ["keywords"],
        "rezumat": ["rezumat"],
        "cuvinte_cheie": ["cuvinte cheie", "cuvinte-cheie"],
        "bibliografie": ["bibliografie", "references", "literatura"]
    }

    all_blocks = []
    for page in doc:
        blocks = page.get_text("blocks")  # fiecare bloc: (x0, y0, x1, y1, text, block_type)
        all_blocks.extend(blocks)

    # Sortare blocuri dupa coordonate verticale (y0)
    all_blocks.sort(key=lambda b: b[1])

    current_section = "body"

    for i, b in enumerate(all_blocks):
        text = b[4].strip()
        if not text:
            continue

        # Primele blocuri: titlu si autori
        if i == 0:
            result["title_ro"] = text
            continue
        elif i == 1:
            result["title_en"] = text
            continue
        elif i == 2:
            result["authors"] = text
            continue

        # Detecteaza sectiuni dupa patterns
        found = False
        for key, keys_list in patterns.items():
            for k in keys_list:
                if k.lower() in text.lower():
                    current_section = key
                    found = True
                    break
            if found:
                break
        if found:
            continue

        # Adauga text in sectiunea curenta
        if current_section in result:
            result[current_section] += text + " "

    # Salvam corpul complet
    result["body"] = " ".join([b[4] for b in all_blocks if b[4].strip() != ""])

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

        slug = str(int(datetime.now().timestamp()))
        conn = sqlite3.connect("db.sqlite")
        cur = conn.cursor()
        cur.execute("INSERT INTO articole (slug, continut_json) VALUES (?,?)",
                    (slug, json.dumps(article_data)))
        conn.commit()
        conn.close()

        # Builder cu datele extrase automat
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

# ---------------- TEMPLATE ZONES ----------------

@app.route("/mapper")
def mapper():
    return render_template("mapper.html", pdf_url="/static/sample.pdf")


@app.route("/save_template", methods=["POST"])
def save_template():
    data = request.json

    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        zones TEXT
    )
    """)

    cur.execute("DELETE FROM templates WHERE name=?", (data["name"],))
    cur.execute("INSERT INTO templates (name, zones) VALUES (?,?)",
                (data["name"], json.dumps(data["zones"])))

    conn.commit()
    conn.close()

    return "OK"
