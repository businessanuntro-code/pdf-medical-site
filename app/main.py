import os

from fastapi import FastAPI, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.storage import save_xml
from app.parser import parse_xml
from app.builder import build_html

app = FastAPI()

templates = Jinja2Templates(directory="templates")


# ---------------- HOME ----------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


# ---------------- UPLOAD ----------------
@app.post("/upload/")
async def upload(file: UploadFile):

    content = await file.read()

    file_id, path = save_xml(content, file.filename)

    data = parse_xml(path)
    html = build_html(data)

    output_path = f"outputs/{file_id}.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return {
        "status": "success",
        "article_url": f"/article/{file_id}"
    }


# ---------------- ARTICLE ----------------
@app.get("/article/{file_id}", response_class=HTMLResponse)
def article(file_id: str):

    path = f"outputs/{file_id}.html"

    if not os.path.exists(path):
        return HTMLResponse("Not found", status_code=404)

    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())
