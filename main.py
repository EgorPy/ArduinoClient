"""
Relay-сервер на FastAPI для управления Arduino через VPS.
Токен передаётся в заголовке в виде XOR-шифра (hex-encoded), а не в открытом виде.

Запуск:
    pip install fastapi uvicorn
    uvicorn app:app --host 0.0.0.0 --port 5000

Как systemd-сервис (пример):
    ExecStart=/usr/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 5000
"""

import threading
from fastapi import FastAPI, Form, Header, HTTPException
from fastapi.responses import PlainTextResponse
from config import REAL_TOKEN, XOR_KEY

app = FastAPI()
lock = threading.Lock()


# Ключ шифрования — та же строка/число должны быть прошиты в Arduino.
# Можно использовать одиночный байт (просто и быстро) или короткую
# многобайтовую фразу для XOR по кругу — так чуть сложнее подобрать.


def xor_decrypt(hex_str: str, key: str) -> str:
    """Расшифровывает hex-строку через XOR с циклическим ключом."""
    try:
        data = bytes.fromhex(hex_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="bad hex")

    key_bytes = key.encode()
    decrypted = bytes(
        b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data)
    )
    try:
        return decrypted.decode()
    except UnicodeDecodeError:
        raise HTTPException(status_code=403, detail="bad token")


def check_token(x_token: str):
    decrypted = xor_decrypt(x_token, XOR_KEY)
    if decrypted != REAL_TOKEN:
        raise HTTPException(status_code=403, detail="forbidden")


ALLOWED_ACTIONS = {"short", "long", "reset", "none"}
state = {"command": "none"}


@app.post("/set_command", response_class=PlainTextResponse)
def set_command(action: str = Form(...), x_token: str = Header(...)):
    check_token(x_token)
    if action not in ALLOWED_ACTIONS:
        raise HTTPException(status_code=400, detail="unknown action")

    with lock:
        state["command"] = action

    return "ok"


@app.get("/poll", response_class=PlainTextResponse)
def poll(x_token: str = Header(...)):
    check_token(x_token)

    with lock:
        cmd = state["command"]
        state["command"] = "none"  # команда выдаётся один раз

    return cmd
