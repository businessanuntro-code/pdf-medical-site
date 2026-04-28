import os
import uuid

from fastapi import FastAPI, UploadFile, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles  # 🔥 IMPORTANT FIX

from app.parser import parse_xml
from app.builder import build_html

app = FastAPI()

templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# =========================
# 🔥 STATIC FILES (IMAGES FIX)
# =========================
app.mount("/static", StaticFiles(directory="uploads"), name="static")


# ---------------- HOME PAGE ----------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


# ---------------- UPLOAD XML ----------------
@app.post("/upload/")
async def upload(file: UploadFile):

    file_id = str(uuid.uuid4())

    # 1. salvare XML
    xml_path = f"{UPLOAD_DIR}/{file_id}.xml"
    content = await file.read()

    with open(xml_path, "wb") as f:
        f.write(content)

    # 2. parse XML
    data = parse_xml(xml_path)

    # 3. generează HTML
    html = build_html(data)

    # 4. salvare articol
    html_path = f"{OUTPUT_DIR}/{file_id}.html"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    # 5. redirect către articol
    return RedirectResponse(
        url=f"/article/{file_id}",
        status_code=302
    )


# ---------------- ARTICLE PAGE ----------------
@app.get("/article/{file_id}", response_class=HTMLResponse)
def article(file_id: str):

    path = f"{OUTPUT_DIR}/{file_id}.html"

    if not os.path.exists(path):
        return HTMLResponse("<h1>Article not found</h1>", status_code=404)

    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())
