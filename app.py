from flask import Flask, request, render_template, redirect, session, send_from_directory
import fitz
import sqlite3
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

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
    CREATE TABLE IF NOT EXISTS template (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        zones TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- SERVE PDF (IMPORTANT) ----------------
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ---------------- EXTRACT ----------------
def extract_with_template(file_path):
    doc = fitz.open(file_path)

    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()
    cur.execute("SELECT zones FROM template LIMIT 1")
    row = cur.fetchone()
    conn.close()

    if not row:
        return {"error": "Nu există template salvat!"}

    zones = json.loads(row[0])
    result = {z["type"]: "" for z in zones}

    for page in doc:
        blocks = page.get_text("blocks")

        for z in zones:
            for b in blocks:
                x0, y0, x1, y1, text, _ = b

                if (
                    x0 >= z["x0"] and
                    x1 <= z["x1"] and
                    y0 >= z["y0"] and
                    y1 <= z["y1"]
                ):
                    result[z["type"]] += text + " "

    return result

# ---------------- ROUTES ----------------

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        file = request.files["pdf"]

        filename = file.filename
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)

        session["pdf_filename"] = filename

        return redirect("/mapper")

    return render_template("home.html")


@app.route("/mapper")
def mapper():
    filename = session.get("pdf_filename")

    if not filename:
        return "Nu există PDF încărcat"

    return render_template(
        "mapper.html",
        pdf_url=f"/uploads/{filename}"
    )


@app.route("/save_template", methods=["POST"])
def save_template():
    zones = request.json

    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute("DELETE FROM template")
    cur.execute(
        "INSERT INTO template (zones) VALUES (?)",
        (json.dumps(zones),)
    )

    conn.commit()
    conn.close()

    return "OK"


@app.route("/generate")
def generate():
    filename = session.get("pdf_filename")

    if not filename:
        return "Nu există PDF"

    path = os.path.join(UPLOAD_FOLDER, filename)

    data = extract_with_template(path)

    html = ""
    for k, v in data.items():
        html += f"<h2>{k}</h2><p>{v}</p>"

    slug = str(int(datetime.now().timestamp()))

    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO articole (slug, continut_html) VALUES (?,?)",
        (slug, html)
    )

    conn.commit()
    conn.close()

    return redirect(f"/view/{slug}")


@app.route("/view/<slug>")
def view(slug):
    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute("SELECT continut_html FROM articole WHERE slug=?", (slug,))
    row = cur.fetchone()

    conn.close()

    if not row:
        return "Articol inexistent"

    html = row[0]

    return f"<div style='max-width:800px;margin:auto'>{html}</div>"


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
