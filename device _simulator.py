# device_simulator.py
import time
import requests
import random
import uuid

API_URL = "http://localhost:8000/api/v1/telemetry"
API_KEY = "devicekey-001"  # should match backend
DEVICE_ID = "device-001"

def generate_reading():
    return {
        "device_id": DEVICE_ID,
        "heart_rate": random.randint(55, 110),
        "spo2": round(random.uniform(90, 99), 1),
        "temperature": round(random.uniform(36.0, 38.5), 1),
        "blood_pressure_sys": random.randint(100, 140),
        "blood_pressure_dia": random.randint(60, 90)
    }

if __name__ == "__main__":
    print("Starting device simulator. Press Ctrl+C to stop.")
    while True:
        payload = generate_reading()
        try:
            resp = requests.post(API_URL, json=payload, params={"api_key": API_KEY}, timeout=5)
            print("Sent:", payload, "->", resp.status_code, resp.text)
        except Exception as e:
            print("Error sending:", e)
        time.sleep(5)  # send every 5 seconds (adjust)
