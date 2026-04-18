import os
import uuid

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_xml(file_bytes, filename):
    file_id = str(uuid.uuid4())
    path = f"{UPLOAD_DIR}/{file_id}.xml"

    with open(path, "wb") as f:
        f.write(file_bytes)

    return file_id, path
