from flask import Flask, request, render_template, redirect, session, url_for, send_from_directory
import os

app = Flask(__name__)
app.secret_key = "supersecret"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Template coordonate selectate
template_data = []

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files.get("pdf_file")
        if not file:
            return "❌ Nu ați selectat PDF"
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)  # ⚡ Salvează fișierul în uploads/
        session["pdf_filename"] = file.filename
        return redirect(url_for("mapper"))
    return render_template("upload.html")

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    # Servește PDF-ul salvat pentru PDF.js
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/mapper")
def mapper():
    filename = session.get("pdf_filename")
    if not filename:
        return redirect(url_for("upload"))
    pdf_url = url_for('uploaded_file', filename=filename)
    field_types = ["title_ro", "title_en", "authors", "abstract", "keywords", "body", "bibliography"]
    return render_template("mapper.html", pdf_url=pdf_url, field_types=field_types)

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

    # Extrage text din zonele selectate (folosind fitz / PyMuPDF)
    import fitz
    doc = fitz.open(path)
    page = doc[0]
    result = {}

    for z in template_data:
        rect = fitz.Rect(z["x0"], z["y0"], z["x1"], z["y1"])
        text = page.get_textbox(rect)
        result[z["type"]] = text.strip()

    # Dacă nu s-au selectat zone, ia tot textul
    if not result:
        result["body"] = page.get_text()

    # Returnează articolul generat
    html = ""
    for k, v in result.items():
        html += f"<h3>{k}</h3><p>{v}</p>"

    return f"<div style='max-width:800px;margin:auto'>{html}</div>"

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
