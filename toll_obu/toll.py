import asyncio
from aiohttp import web
import sqlite3
import paho.mqtt.client as mqtt
from datetime import datetime
from config.settings import MQTT_BROKER, TOPICS, VIN, on_connect

# Vehicle Identification Number (VIN)
VEHICLE_VIN = VIN

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.connect(MQTT_BROKER)

# Database Initialization
def initialize_db():
    connection = sqlite3.connect("smart_vehicle.db")
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS toll_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gate_id TEXT NOT NULL,
            event_time DATETIME NOT NULL
        )
    """)
    connection.commit()
    connection.close()

# Function to log toll gate events
def log_toll_event(gate_id):
    connection = sqlite3.connect("smart_vehicle.db")
    cursor = connection.cursor()
    event_time = datetime.now()
    cursor.execute(
        "INSERT INTO toll_events (gate_id, event_time) VALUES (?, ?)",
        (gate_id, event_time)
    )
    connection.commit()
    connection.close()
    # print(f"Toll gate {gate_id} event logged at {event_time}.")
    return event_time

# Handler for toll gate requests
async def toll_awake_handler(request):
    gate_id = request.match_info.get("gate_id")
    if not gate_id:
        return web.Response(status=400, text="GATE-ID is required.")

    event_time = log_toll_event(gate_id)

    mqtt_message = f"Gate {gate_id} awakened TollOBU at {event_time}"
    mqtt_client.publish(TOPICS["TOLL_SYSTEM"], mqtt_message)

    # print(f"Published to vc2425/toll-system: {mqtt_message}")
    return web.Response(text=VEHICLE_VIN)

# Fetch all logged toll events (for testing/debugging)
async def fetch_toll_events_handler(request):
    connection = sqlite3.connect("smart_vehicle.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM toll_events ORDER BY event_time DESC")
    events = cursor.fetchall()
    connection.close()

    return web.json_response({"toll_events": events})

# App initialization and routes
app = web.Application()
app.router.add_get("/toll-awake/{gate_id}", toll_awake_handler)  # Entrance/exit gate handler
app.router.add_get("/toll-events", fetch_toll_events_handler)   # Fetch toll events (debugging)

if __name__ == "__main__":
    initialize_db()
    mqtt_client.loop_start()
    web.run_app(app, port=8082)
