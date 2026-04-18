import os
import uuid

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_upload(file):
    file_id = str(uuid.uuid4())
    path = f"{UPLOAD_DIR}/{file_id}.xml"

    with open(path, "wb") as f:
        f.write(file)

    return file_id, path


def save_html(file_id, html):
    path = f"{OUTPUT_DIR}/{file_id}.html"

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    return path
