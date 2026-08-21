"""
Relay-сервер на FastAPI для управления Arduino через VPS.

Запуск:
    pip install fastapi uvicorn
    uvicorn app:app --host 0.0.0.0 --port 5000

Как systemd-сервис (пример):
    ExecStart=/usr/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 5000
"""

import threading
from fastapi import FastAPI, Form, Query, HTTPException
from fastapi.responses import PlainTextResponse
from config import TOKEN

app = FastAPI()
lock = threading.Lock()

ALLOWED_ACTIONS = {"short", "long", "reset", "none"}

state = {"command": "none"}


def check_token(token: str):
    if token != TOKEN:
        raise HTTPException(status_code=403, detail="forbidden")


@app.post("/set_command", response_class=PlainTextResponse)
def set_command(token: str = Form(...), action: str = Form(...)):
    check_token(token)
    if action not in ALLOWED_ACTIONS:
        raise HTTPException(status_code=400, detail="unknown action")

    with lock:
        state["command"] = action

    return "ok"


@app.get("/poll", response_class=PlainTextResponse)
def poll(token: str = Query(...)):
    check_token(token)

    with lock:
        cmd = state["command"]
        state["command"] = "none"  # команда выдаётся один раз

    return cmd
