# app/crud.py
from sqlmodel import select
from .models import Telemetry, Device
from datetime import datetime

def create_telemetry(session, telem: Telemetry):
    session.add(telem)
    session.commit()
    session.refresh(telem)
    return telem

def list_recent_telemetry(session, limit: int = 100):
    q = select(Telemetry).order_by(Telemetry.timestamp.desc()).limit(limit)
    return session.exec(q).all()

def get_device_by_api_key(session, api_key: str):
    q = select(Device).where(Device.api_key == api_key)
    return session.exec(q).first()

def create_device(session, device: Device):
    session.add(device)
    session.commit()
    session.refresh(device)
    return device

def get_device_by_id(session, device_id: str):
    q = select(Device).where(Device.device_id == device_id)
    return session.exec(q).first()
