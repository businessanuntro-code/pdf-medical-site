from flask import Flask, request, render_template, redirect, session, url_for
import fitz
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecret"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Template salvat temporar in memoria serverului
template_data = []

# Salvează articole generate (temporar, fără DB)
ARTICOLE_FOLDER = "articole"
os.makedirs(ARTICOLE_FOLDER, exist_ok=True)
articles_list = []  # Lista de articole generate

# ---------------- PDF ----------------
def extract_with_template(file_path):
    doc = fitz.open(file_path)
    page = doc[0]
    result = {}

    for z in template_data:
        rect = fitz.Rect(z["x0"], z["y0"], z["x1"], z["y1"])
        text = page.get_textbox(rect)
        result[z["type"]] = text.strip()

    # Dacă nu există zone → ia tot textul
    if not result:
        result["body"] = page.get_text()
    return result

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    # Trimite lista de articole generate
    return render_template("home.html", articles=articles_list)

@app.route("/upload", methods=["GET","POST"])
def upload():
    if request.method == "POST":
        if "pdf_file" not in request.files:
            return "❌ Nu a fost selectat niciun fișier PDF"
        file = request.files["pdf_file"]
        if file.filename == "":
            return "❌ Nume fișier invalid"
        
        # Salvează PDF-ul în folderul uploads
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        session["pdf_filename"] = file.filename
        pdf_url = url_for('uploaded_file', filename=file.filename)
        return render_template("mapper.html", pdf_url=pdf_url, field_types=[
            "title_ro", "title_en", "authors", "abstract", "keywords", "rezumat", "cuvinte_cheie", "body", "bibliografie"
        ])
    return render_template("upload.html")

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    # Servește fișierul PDF din folderul uploads
    return redirect(f"/{UPLOAD_FOLDER}/{filename}")

@app.route("/save_template", methods=["POST"])
def save_template():
    global template_data
    template_data = request.json
    return "ok"

@app.route("/generate")
def generate():
    filename = session.get("pdf_filename")
    if not filename:
        return "❌ Nu există PDF încărcat"

    path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(path):
        return "❌ Fișierul PDF nu există pe server"

    data = extract_with_template(path)

    html = ""
    for k,v in data.items():
        html += f"<h3>{k}</h3><p>{v}</p>"

    # Salvăm articolul într-un fișier temporar
    slug = str(int(datetime.now().timestamp()))
    articole_path = os.path.join(ARTICOLE_FOLDER, f"{slug}.html")
    with open(articole_path, "w", encoding="utf-8") as f:
        f.write(html)

    # Adăugăm articolul în lista vizibilă pe home
    articles_list.append({
        "slug": slug,
        "pdf_filename": filename,
        "html_path": articole_path
    })

    return redirect(f"/view/{slug}")

@app.route("/view/<slug>")
def view(slug):
    articole = [a for a in articles_list if a["slug"] == slug]
    if not articole:
        return "❌ Articol inexistent"

    with open(articole[0]["html_path"], "r", encoding="utf-8") as f:
        html = f.read()

    return f"<div style='max-width:800px;margin:auto'>{html}</div>"

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
