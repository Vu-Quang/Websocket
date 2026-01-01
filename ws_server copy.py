import uvicorn
import time
import asyncio
from typing import Dict, Set
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi import WebSocket, WebSocketDisconnect
import jwt
from jwt_auth import verify_jwt
from pydantic import BaseModel

# ==========================================================
# CONFIG
# ==========================================================
SECRET = "SECRET123"
ALGO = "HS256"
IDLE_TIMEOUT = 60  # seconds, auto disconnect idle websockets

# ==========================================================
# CONNECTION WRAPPER
# ==========================================================
class Connection:
    """Store WebSocket and last activity timestamp."""
    def __init__(self, websocket: WebSocket):
        self.ws = websocket
        self.last_active = time.time()

# ==========================================================
# LIFESPAN — REPLACES on_event()
# ==========================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting WebSocket server...")

    # State
    app.state.channels: Dict[str, Set[Connection]] = {}

    # Background cleanup
    async def cleanup_task():
        while True:
            now = time.time()
            to_remove_channels = []

            for channel, connections in list(app.state.channels.items()):
                dead_connections = []
                for conn in list(connections):
                    if now - conn.last_active > IDLE_TIMEOUT:
                        print(f"Auto-closing idle connection in channel '{channel}'")
                        try:
                            await conn.ws.close()
                        except:
                            pass
                        dead_connections.append(conn)

                for dead in dead_connections:
                    connections.remove(dead)

                # Remove empty channels
                if len(connections) == 0:
                    print(f"Removing empty channel: {channel}")
                    to_remove_channels.append(channel)

            for ch in to_remove_channels:
                del app.state.channels[ch]

            await asyncio.sleep(10)

    cleanup = asyncio.create_task(cleanup_task())

    # Hand over to the app
    yield

    # Shutdown
    cleanup.cancel()
    print("Stopping WebSocket server...")
    for channel, conns in app.state.channels.items():
        for conn in conns:
            try:
                await conn.ws.close()
            except:
                pass


app = FastAPI(lifespan=lifespan)


# ==========================================================
# MODELS FOR WEBHOOK (from Odoo)
# ==========================================================
class PushMessage(BaseModel):
    channel: str
    message: str


# ==========================================================
# WEBHOOK API — Odoo CALLS HERE
# ==========================================================
@app.post("/send")
async def send_message(data: PushMessage):
    channels = app.state.channels
    ch = data.channel

    if ch not in channels:
        return {"status": "no_subscribers"}

    dead = []
    for conn in list(channels[ch]):
        try:
            await conn.ws.send_text(data.message)
        except:
            dead.append(conn)

    for d in dead:
        channels[ch].remove(d)

    # Cleanup if channel empty
    if len(channels[ch]) == 0:
        del channels[ch]

    return {"status": "ok", "receivers": len(channels.get(ch, []))}


# ==========================================================
# WEBSOCKET ENTRYPOINT
# ==========================================================
@app.websocket("/ws/order_123")
async def websocket_endpoint(websocket: WebSocket, channel: str):
    print(f"Client connecting to channel '{channel}'")
    token = websocket.query_params.get("token")

    if not token or not verify_jwt(token):
        await websocket.close(code=4401)
        return

    await websocket.accept()

    conn = Connection(websocket)
    channels = app.state.channels
    channels.setdefault(channel, set()).add(conn)

    print(f"Client joined channel '{channel}'")

    try:
        while True:
            msg = await websocket.receive_text()
            conn.last_active = time.time()  # update activity

            # echo for testing
            await websocket.send_text(f"OK: {msg}")

    except WebSocketDisconnect:
        print(f"Client disconnected from channel '{channel}'")

    # Remove from channel
    try:
        channels[channel].remove(conn)
        if len(channels[channel]) == 0:
            del channels[channel]
    except KeyError:
        pass

# ====================================
#            RUN SERVER
# ====================================
if __name__ == "__main__":
    uvicorn.run("ws_server:app", host="0.0.0.0", port=9000, reload=True)