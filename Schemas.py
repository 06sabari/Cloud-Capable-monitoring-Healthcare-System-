# app/schemas.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TelemetryCreate(BaseModel):
    device_id: str
    heart_rate: Optional[int] = None
    spo2: Optional[float] = None
    temperature: Optional[float] = None
    blood_pressure_sys: Optional[int] = None
    blood_pressure_dia: Optional[int] = None
    timestamp: Optional[datetime] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
