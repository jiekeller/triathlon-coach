from fastapi import APIRouter
from pydantic import BaseModel
from db import get_conn
from agent import run_agent

router = APIRouter()


class ChatRequest(BaseModel):
    user_id: str
    message: str


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

    # Append new user message
    history.append({"role": "user", "content": req.message})

    # Save user message
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
