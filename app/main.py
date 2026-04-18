from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# ---------------- HOME ----------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


# ---------------- UPLOAD (placeholder acum) ----------------
@app.post("/upload/")
async def upload(file: UploadFile):
    content = await file.read()

    return {
        "status": "ok",
        "filename": file.filename,
        "size": len(content)
    }
