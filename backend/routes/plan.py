import base64
import io
import pdfplumber
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from db import get_conn

router = APIRouter()

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "text/plain",
}


# ---------- Training plan upload (PDF → extracted text) ----------

@router.post("/upload-plan")
async def upload_plan(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    race_date: str = Form(...),
    race_type: str = Form(...),
):
    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse(status_code=400, content={"error": "Only PDF files are supported for training plans"})

    contents = await file.read()
    with pdfplumber.open(io.BytesIO(contents)) as pdf:
        text = "\n\n".join(page.extract_text() or "" for page in pdf.pages).strip()

    if not text:
        return JSONResponse(status_code=400, content={"error": "Could not extract text from PDF"})

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO training_plans (user_id, plan, race_date, race_type)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE
        SET plan=EXCLUDED.plan, race_date=EXCLUDED.race_date,
            race_type=EXCLUDED.race_type, updated_at=NOW()
    """, (user_id, text, race_date, race_type))
    conn.commit()
    cur.close()
    conn.close()

    return {"saved": True, "characters": len(text)}


# ---------- Generic file upload ----------

@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Form(...),
):
    mime = file.content_type or ""

    # Normalise common cases browsers get wrong
    if file.filename.lower().endswith(".pdf"):
        mime = "application/pdf"
    elif file.filename.lower().endswith(".txt"):
        mime = "text/plain"

    if mime not in ALLOWED_MIME_TYPES:
        return JSONResponse(
            status_code=400,
            content={"error": f"Unsupported file type '{mime}'. Allowed: PDF, images (jpg/png/gif/webp), txt."},
        )

    contents = await file.read()
    data_b64 = base64.b64encode(contents).decode("utf-8")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO user_files (user_id, filename, mime_type, data_base64) VALUES (%s, %s, %s, %s) RETURNING id",
        (user_id, file.filename, mime, data_b64),
    )
    file_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()

    return {"saved": True, "id": file_id, "filename": file.filename, "mime_type": mime}


@router.get("/files/{user_id}")
def list_files(user_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, filename, mime_type, created_at FROM user_files WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"files": [{"id": r["id"], "filename": r["filename"], "mime_type": r["mime_type"], "created_at": str(r["created_at"])} for r in rows]}


@router.delete("/files/{file_id}")
def delete_file(file_id: int, user_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM user_files WHERE id = %s AND user_id = %s", (file_id, user_id))
    conn.commit()
    cur.close()
    conn.close()
    return {"deleted": True}


# ---------- Plan read ----------

@router.get("/plan/{user_id}")
def get_plan(user_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT plan, race_date, race_type, updated_at FROM training_plans WHERE user_id = %s",
        (user_id,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return {"plan": None}
    return {
        "plan": row["plan"][:500] + "..." if len(row["plan"]) > 500 else row["plan"],
        "race_date": str(row["race_date"]),
        "race_type": row["race_type"],
        "updated_at": str(row["updated_at"]),
    }
