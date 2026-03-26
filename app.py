from flask import Flask, request, render_template, redirect, session, url_for, send_from_directory
import fitz
import os
import json

app = Flask(__name__)
app.secret_key = "supersecret"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Template coordonate selectate
template_data = []

# ---------------- PDF ----------------
def extract_with_template(file_path):
    """Extrage textul din PDF pe baza coordonatelor salvate în template_data"""
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

    # Dacă nu există zone selectate, ia tot textul
    if not result:
        result["body"] = ""
        for page in doc:
            result["body"] += page.get_text()

    return result

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/upload", methods=["GET","POST"])
def upload():
    if request.method == "POST":
        file = request.files.get("pdf_file")
        if not file:
            return "❌ Nu ați selectat PDF"
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)
        session["pdf_filename"] = file.filename
        return redirect(url_for("mapper"))
    return render_template("upload.html")

@app.route("/mapper")
def mapper():
    """Pagina de selecție coordonate PDF"""
    filename = session.get("pdf_filename")
    if not filename:
        return redirect(url_for("upload"))
    pdf_url = url_for('uploaded_file', filename=filename)
    # Tipuri predefinite pentru selectare
    field_types = ["title_ro", "title_en", "authors", "abstract", "keywords", "body", "bibliography"]
    return render_template("mapper.html", pdf_url=pdf_url, field_types=field_types)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    """Servește PDF-ul încărcat direct pentru PDF.js"""
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/save_template", methods=["POST"])
def save_template():
    """Salvează coordonatele selectate de utilizator"""
    global template_data
    template_data = request.json
    return "ok"

@app.route("/generate")
def generate():
    """Generează articolul HTML pe baza coordonatelor selectate"""
    filename = session.get("pdf_filename")
    if not filename:
        return "❌ Nu există PDF încărcat"
    path = os.path.join(UPLOAD_FOLDER, filename)
    data = extract_with_template(path)

    html = ""
    for k, v in data.items():
        html += f"<h3>{k}</h3><p>{v}</p>"

    return f"<div style='max-width:800px;margin:auto'>{html}</div>"

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
