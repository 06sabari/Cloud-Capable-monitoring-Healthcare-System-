# app/main.py
from fastapi import FastAPI, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session
from .database import init_db, get_session
from .models import Telemetry, Device
from .schemas import TelemetryCreate, Token
from .crud import create_telemetry, list_recent_telemetry, create_device, get_device_by_id, get_device_by_api_key
from .auth import verify_device_api_key, create_access_token, get_current_token
from datetime import datetime
from typing import List
import uuid
import asyncio
from fastapi.templating import Jinja2Templates
import os

app = FastAPI(title="Cloud Healthcare Monitor API")

# init DB on startup
@app.on_event("startup")
def on_startup():
    init_db()
    # Create a default device for testing (only if not exists)
    with next(get_session()) as session:
        d = get_device_by_id(session, "device-001")
        if not d:
            api_key = "devicekey-001"  # in production generate securely
            create_device(session, Device(device_id="device-001", api_key=api_key, label="Test Device"))

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# In-memory list of websockets
class ConnectionManager:
    def __init__(self):
        self.connections: List[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        self.connections.remove(websocket)
    async def broadcast(self, message: dict):
        living = []
        for ws in list(self.connections):
            try:
                await ws.send_json(message)
                living.append(ws)
            except Exception:
                try: ws.close()
                except: pass
        self.connections = living

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/api/v1/telemetry", status_code=201)
async def post_telemetry(payload: TelemetryCreate, api_key: str = None, session: Session = Depends(get_session)):
    """
    Devices should POST telemetry JSON. Two options to authenticate:
    1) send ?api_key=... query param (simple)
    2) Or we can add header-based auth if desired.
    """
    # Basic api_key check
    if not api_key:
        raise HTTPException(status_code=401, detail="api_key required")
    device = get_device_by_api_key(session, api_key)
    if not device:
        raise HTTPException(status_code=401, detail="invalid api_key")

    telem = Telemetry(
        device_id=payload.device_id,
        heart_rate=payload.heart_rate,
        spo2=payload.spo2,
        temperature=payload.temperature,
        blood_pressure_sys=payload.blood_pressure_sys,
        blood_pressure_dia=payload.blood_pressure_dia,
        timestamp=payload.timestamp or datetime.utcnow()
    )
    created = create_telemetry(session, telem)
    # push to WebSocket clients
    await manager.broadcast({
        "id": created.id,
        "device_id": created.device_id,
        "heart_rate": created.heart_rate,
        "spo2": created.spo2,
        "temperature": created.temperature,
        "blood_pressure_sys": created.blood_pressure_sys,
        "blood_pressure_dia": created.blood_pressure_dia,
        "timestamp": created.timestamp.isoformat()
    })
    return {"status": "ok", "id": created.id}

@app.get("/api/v1/telemetry/recent")
def get_recent(limit: int = 50, session: Session = Depends(get_session)):
    items = list_recent_telemetry(session, limit=limit)
    return items

@app.get("/api/v1/devices")
def list_devices(session: Session = Depends(get_session)):
    from sqlmodel import select
    q = select(Device)
    return session.exec(q).all()

# WebSocket endpoint for live telemetry
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # keep connection alive; optionally receive pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
