from flask import Flask, request, render_template, redirect, session, url_for, send_from_directory
import fitz
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecret"

# Folder unde salvăm PDF-urile
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Template salvat temporar in memoria serverului (coordonate)
template_data = []

# ---------------- PDF ----------------
def extract_with_template(file_path):
    """
    Extrage textul din PDF folosind template_data (coordonate selectate).
    Daca nu sunt coordonate, preia tot textul din toate paginile.
    """
    doc = fitz.open(file_path)
    result = {}

    for page in doc:
        for z in template_data:
            rect = fitz.Rect(z["x0"], z["y0"], z["x1"], z["y1"])
            text = page.get_textbox(rect)
            if z["type"] in result:
                result[z["type"]] += "\n" + text.strip()
            else:
                result[z["type"]] = text.strip()

    # Daca nu exista zone → ia tot textul
    if not result:
        result["body"] = ""
        for page in doc:
            result["body"] += page.get_text()
    return result

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    """Pagina principala"""
    return render_template("home.html")

@app.route("/upload", methods=["GET","POST"])
def upload():
    """
    Upload PDF si deschidere mapper.
    PDF-ul este salvat in folderul uploads/
    """
    if request.method == "POST":
        file = request.files.get("pdf_file")
        if not file:
            return "❌ Nu ați selectat niciun fișier PDF"

        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)
        session["pdf_filename"] = file.filename

        pdf_url = url_for('uploaded_file', filename=file.filename)
        return render_template("mapper.html", pdf_url=pdf_url)

    return render_template("upload.html")

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    """Serveste PDF-ul uploadat pentru vizualizare in mapper"""
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/save_template", methods=["POST"])
def save_template():
    """Salveaza coordonatele selectate in mapper"""
    global template_data
    template_data = request.json
    return "ok"

@app.route("/generate")
def generate():
    """Genereaza articolul folosind PDF-ul uploadat si template-ul salvat"""
    filename = session.get("pdf_filename")
    if not filename:
        return "❌ Nu există PDF încărcat"

    path = os.path.join(UPLOAD_FOLDER, filename)
    data = extract_with_template(path)

    html = ""
    for k,v in data.items():
        html += f"<h3>{k}</h3><p>{v}</p>"

    return f"<div style='max-width:800px;margin:auto'>{html}</div>"

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
