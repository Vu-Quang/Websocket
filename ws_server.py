# ws_server.py
import uvicorn, time, asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
import json
from typing import Dict, List
from jwt_auth import verify_jwt
from contextlib import asynccontextmanager
from config import CORS_CONFIG, ENV

print(f"Starting WS server in {ENV} mode with CORS:", CORS_CONFIG)


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


from pydantic import BaseModel
from typing import Any

class WebhookPayload(BaseModel):
    channel: str
    message: Any


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     print("Starting WebSocket server...")

#     # State
#     app.channels: Dict[str, List[Connection]] = {}

#     # Background cleanup
#     async def cleanup_task():
#         while True:
#             now = time.time()
#             to_remove_channels = []

#             for channel, connections in list(app.channels.items()):
#                 dead_connections = []
#                 for conn in list(connections):
#                     if now - conn.last_active > IDLE_TIMEOUT:
#                         print(f"Auto-closing idle connection in channel '{channel}'")
#                         try:
#                             await conn.ws.close()
#                         except:
#                             pass
#                         dead_connections.append(conn)

#                 for dead in dead_connections:
#                     connections.remove(dead)

#                 # Remove empty channels
#                 if len(connections) == 0:
#                     print(f"Removing empty channel: {channel}")
#                     to_remove_channels.append(channel)

#             for ch in to_remove_channels:
#                 del app.state.channels[ch]

#             await asyncio.sleep(10)

#     cleanup = asyncio.create_task(cleanup_task())

#     # Hand over to the app
#     yield

#     # Shutdown
#     cleanup.cancel()
#     print("Stopping WebSocket server...")
#     for channel, conns in app.state.channels.items():
#         for conn in conns:
#             try:
#                 await conn.ws.close()
#             except:
#                 pass


app = FastAPI(title="WebSocket Service",
              description="WS hub + webhook from Odoo + JWT Auth")

# Allow FE apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Channel → list of WebSocket connections
channels: Dict[str, List[WebSocket]] = {}

def get_channel(name: str) -> List[WebSocket]:
    if name not in channels:
        channels[name] = []
    return channels[name]

# ====================================
#            WebSocket
# ====================================
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):

    token = ws.query_params.get("token")

    # if not token:
    #     await ws.close(code=4401, reason="Missing token")
    #     return

    # # 🔐 Verify JWT
    # try:
    #     claims = verify_jwt(token)
    # except Exception as e:
    #     await ws.close(code=4401, reason=str(e))
    #     return

    # order_id = claims.get("order_id")

    # print(f"WS Connected to Order {order_id}")


    await ws.accept()
    subscribed_channels = []

    try:
        while True:
            data = await ws.receive_text()
            payload = json.loads(data)

            # Client subscribes to channel list
            if payload.get("type") == "subscribe":
                for ch in payload.get("channels", []):
                    get_channel(ch).append(ws)
                    subscribed_channels.append(ch)
                    print(f"Client subscribed to {ch}")

            # Heartbeat
            if payload.get("type") == "ping":
                await ws.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass

    finally:
        # Cleanup on disconnect
        for ch in subscribed_channels:
            if ws in channels[ch]:
                channels[ch].remove(ws)
        print("Client disconnected")

# ====================================
#            WEBHOOK
# ====================================
@app.get("/health")
async def webhook(request: Request):
    return {
        "status": "ok"
    }

@app.post("/webhook")
async def webhook(payload: WebhookPayload):
    print("Webhook received:", payload.model_dump())

    channel = payload.channel
    message = payload.message

    if not channel:
        return {"error": "Missing 'channel'"}

    conns = get_channel(channel)
    closed_clients = []

    for ws in conns:
        try:
            # Gửi tin
            await ws.send_json({
                "type": "odoo_push",
                "channel": channel,
                "payload": message,
            })

            # =====================
            #   ĐÓNG KẾT NỐI SAU GỬI
            # =====================
            await ws.close()

        except:
            pass

        closed_clients.append(ws)

    # Cleanup
    for ws in closed_clients:
        if ws in conns:
            conns.remove(ws)

    return {
        "status": "ok",
        "sent": len(closed_clients),
        "channel": channel,
    }

# ====================================
#            RUN SERVER
# ====================================
if __name__ == "__main__":
    uvicorn.run("ws_server:app", host="0.0.0.0", port=9000, reload=True)
