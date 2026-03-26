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
        name TEXT,
        zones TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- EXTRACT CU TEMPLATE ----------------
def extract_with_template(file_stream):
    doc = fitz.open(stream=file_stream.read(), filetype="pdf")

    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute("SELECT zones FROM templates WHERE name='default'")
    row = cur.fetchone()

    if not row:
        return {"body": "Nu exista template definit!"}

    zones = json.loads(row[0])
    conn.close()

    result = {}

    # initializeaza campuri
    for z in zones:
        result[z["type"]] = ""

    # parcurge toate paginile
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
            article_data = extract_with_template(f)

        # transforma in HTML simplu
        html = ""
        for k, v in article_data.items():
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

    return render_template("upload.html")


@app.route("/view/<slug>")
def view(slug):
    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute("SELECT continut_html FROM articole WHERE slug=?", (slug,))
    html = cur.fetchone()[0]

    conn.close()

    return f"<div style='max-width:800px;margin:auto'>{html}</div>"


# ---------------- MAPPER ----------------

@app.route("/mapper")
def mapper():
    return render_template("mapper.html", pdf_url="/static/sample.pdf")


@app.route("/save_template", methods=["POST"])
def save_template():
    data = request.json

    conn = sqlite3.connect("db.sqlite")
    cur = conn.cursor()

    cur.execute("DELETE FROM templates WHERE name=?", (data["name"],))
    cur.execute(
        "INSERT INTO templates (name, zones) VALUES (?,?)",
        (data["name"], json.dumps(data["zones"]))
    )

    conn.commit()
    conn.close()

    return "OK"


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
