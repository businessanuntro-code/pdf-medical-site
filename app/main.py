from fastapi import FastAPI, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.parser import parse_xml
from app.builder import build_html
from app.storage import save_upload, save_html

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


# ---------------- HOME PAGE ----------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ---------------- UPLOAD XML ----------------
@app.post("/upload/")
async def upload(file: UploadFile):

    content = await file.read()

    file_id, path = save_upload(content)

    data = parse_xml(path)
    html = build_html(data, file_id)

    save_html(file_id, html)

    return {
        "status": "success",
        "article_url": f"/article/{file_id}"
    }


# ---------------- ARTICLE PAGE ----------------
@app.get("/article/{file_id}", response_class=HTMLResponse)
def article(request: Request, file_id: str):

    path = f"outputs/{file_id}.html"

    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    return HTMLResponse(content=html)
