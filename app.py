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
                "id": len(blocks),
                "text": text,
                "size": size,
                "x": b["bbox"][0],
                "y": b["bbox"][1]
            })

    return blocks

# -------------------- APPLY TEMPLATE --------------------
def apply_template(blocks, template):
    sections = {
        "title_ro": "",
        "title_en": "",
        "autori": "",
        "abstract": "",
        "abstract_text": "",
        "keywords": "",
        "keywords_list": "",
        "rezumat": "",
        "rezumat_text": "",
        "cuvinte_cheie": "",
        "cuvinte_cheie_list": "",
        "text": []
    }

    for b in blocks:
        role = template.get(str(b["id"]))

        if role == "ignore":
            continue

        if role == "title_ro":
            sections["title_ro"] = b["text"]

        elif role == "title_en":
            sections["title_en"] = b["text"]

        elif role == "autori":
            sections["autori"] += b["text"] + " "

        elif role == "abstract":
            sections["abstract"] = b["text"]

        elif role == "abstract_text":
            sections["abstract_text"] += b["text"] + " "

        elif role == "keywords":
            sections["keywords"] = b["text"]

        elif role == "keywords_list":
            sections["keywords_list"] = b["text"]

        elif role == "rezumat":
            sections["rezumat"] = b["text"]

        elif role == "rezumat_text":
            sections["rezumat_text"] += b["text"] + " "

        elif role == "cuvinte_cheie":
            sections["cuvinte_cheie"] = b["text"]

        elif role == "cuvinte_cheie_list":
            sections["cuvinte_cheie_list"] = b["text"]

        else:
            sections["text"].append(b["text"])

    # 🔥 HTML FINAL ORDONAT (MODEL MEDICHUB)
    html = f"""
    <h1>{sections['title_ro']}</h1>
    <p><em>{sections['title_en']}</em></p>

    <p><strong>{sections['autori']}</strong></p>

    <h2>{sections['abstract']}</h2>
    <p>{sections['abstract_text']}</p>

    <p><strong>{sections['keywords']}</strong>: {sections['keywords_list']}</p>

    <h2>{sections['rezumat']}</h2>
    <p>{sections['rezumat_text']}</p>

    <p><strong>{sections['cuvinte_cheie']}</strong>: {sections['cuvinte_cheie_list']}</p>
    """

    for t in sections["text"]:
        html += f"<p>{t}</p>"

    return html


# -------------------- ROUTES --------------------
@app.route("/")
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

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        with open(filepath, "rb") as f:
            blocks = extract_blocks(f)

        with open("last_blocks.json", "w") as f:
            json.dump(blocks, f)

        return render_template("calibrate.html", blocks=blocks)

    return render_template("upload.html")


@app.route("/save_template", methods=["POST"])
def save_template():
    selections = request.form.to_dict()

    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute("DELETE FROM templates")
    cur.execute("INSERT INTO templates (reguli) VALUES (?)", (json.dumps(selections),))

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

    slug = str(int(datetime.now().timestamp()))

    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO articole (titlu, slug, continut_html) VALUES (?, ?, ?)",
        ("articol", slug, html)
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
