from fastapi import APIRouter
from pydantic import BaseModel
from db import get_conn
from agent import run_agent

router = APIRouter()


class ChatRequest(BaseModel):
    user_id: str
    message: str


def _load_user_files(user_id: str) -> list[dict]:
    """Return the 10 most recent uploaded files as Claude content blocks."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """SELECT filename, mime_type, data_base64
           FROM user_files WHERE user_id = %s
           ORDER BY created_at DESC LIMIT 10""",
        (user_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    blocks = []
    for r in rows:
        mime = r["mime_type"]
        if mime.startswith("image/"):
            blocks.append({
                "type": "image",
                "source": {"type": "base64", "media_type": mime, "data": r["data_base64"]},
            })
        elif mime == "application/pdf":
            blocks.append({
                "type": "document",
                "source": {"type": "base64", "media_type": "application/pdf", "data": r["data_base64"]},
                "title": r["filename"],
            })
        elif mime == "text/plain":
            import base64
            text = base64.b64decode(r["data_base64"]).decode("utf-8", errors="replace")
            blocks.append({"type": "text", "text": f"[File: {r['filename']}]\n{text}"})

    return blocks


@router.post("/chat")
def chat(req: ChatRequest):
    conn = get_conn()
    cur = conn.cursor()

    # Load conversation history
    cur.execute(
        "SELECT role, content FROM conversations WHERE user_id = %s ORDER BY created_at ASC",
        (req.user_id,),
    )
    history = [{"role": r["role"], "content": r["content"]} for r in cur.fetchall()]

    # Build the current user message — prepend uploaded files so Claude can see them
    file_blocks = _load_user_files(req.user_id)
    if file_blocks:
        user_content = file_blocks + [{"type": "text", "text": req.message}]
    else:
        user_content = req.message

    history.append({"role": "user", "content": user_content})

    # Save user message text only (we re-attach files each request)
    cur.execute(
        "INSERT INTO conversations (user_id, role, content) VALUES (%s, %s, %s)",
        (req.user_id, "user", req.message),
    )
    conn.commit()

    # Run the agent
    reply = run_agent(req.user_id, history)

    # Save assistant reply
    cur.execute(
        "INSERT INTO conversations (user_id, role, content) VALUES (%s, %s, %s)",
        (req.user_id, "assistant", reply),
    )
    conn.commit()
    cur.close()
    conn.close()

    return {"reply": reply}


@router.delete("/chat/{user_id}")
def clear_history(user_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM conversations WHERE user_id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"cleared": True}
