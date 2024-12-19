import asyncio
from datetime import date, datetime
from aiohttp import web
import sqlite3
import paho.mqtt.client as mqtt
from config.settings import MQTT_BROKER, TOPICS, on_connect

def on_message(client, userdata, msg):
    print(f"Message received: {msg.topic} - {msg.payload.decode()}")

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER)

# Database Initialization
def initialize_db():
    connection = sqlite3.connect('smart_vehicle.db')
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            driver_id TEXT PRIMARY KEY,
            token TEXT NOT NULL
        )
    ''')
    connection.commit()
    connection.close()

# Function to add a new driver to the database
def add_driver(driver_id, token):
    connection = sqlite3.connect('smart_vehicle.db')
    cursor = connection.cursor()
    cursor.execute("INSERT OR REPLACE INTO drivers (driver_id, token) VALUES (?, ?)", (driver_id, token))
    connection.commit()
    connection.close()
    print(f"Driver {driver_id} added to the database.")


# Function to fetch all drivers from the database
def fetch_drivers():
    connection = sqlite3.connect('smart_vehicle.db')
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM drivers")
    drivers = cursor.fetchall()
    connection.close()
    return drivers


def entry_attempts():
    connection = sqlite3.connect('smart_vehicle.db')
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entry_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id TEXT NOT NULL,
            token TEXT NOT NULL,
            created_at DATETIME NOT NULL
        )
    ''')
    connection.commit()
    connection.close()


def add_attempts(driver_id, token):
    connection = sqlite3.connect('smart_vehicle.db')
    cursor = connection.cursor()
    created_at = datetime.now()  # Get the current date
    cursor.execute(
        "INSERT OR REPLACE INTO entry_attempts (driver_id, token, created_at) VALUES (?, ?, ?)",
        (driver_id, token, created_at)
    )
    connection.commit()
    connection.close()


def latest_attempt():
    connection = sqlite3.connect('smart_vehicle.db')
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM entry_attempts ORDER BY created_at DESC LIMIT 1")
    driver = cursor.fetchone()
    connection.close()
    print(driver)
    return driver

# Function to check if the driver is authorized
def is_authorized(driver_id, token):
    connection = sqlite3.connect('smart_vehicle.db')
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM drivers WHERE driver_id = ? AND token = ?", (driver_id, token))
    result = cursor.fetchone()
    connection.close()
    return result is not None

# Handler for the keyless entry system
async def keyless_handler(request):
    global last_driver
    data = await request.json()
    driver_id = data.get("driver_id")
    token = data.get("token")

    # if the driver is authorized
    if is_authorized(driver_id, token):
        add_attempts(driver_id, token)

        mqtt_message = f"{driver_id} authorized"
        mqtt_client.publish(TOPICS["KEYLESS_ACCEPTED"], mqtt_message)
        # print(f"Published to vc2425/keyless-accepted: {mqtt_message}")
        return web.Response(text="Vehicle Unlocked")
    else:
        add_attempts(driver_id, token)
        mqtt_message = f"{driver_id} is unauthorized"
        mqtt_client.publish(TOPICS["KEYLESS_ERROR"], mqtt_message)
        # print(f"Published to vc2425/keyless-error: {mqtt_message}")
        return web.Response(status=401, text="Unauthorized")
    
# Handler to close the keyless entry system
async def keyless_close_handler(request):
    data = await request.json()
    driver_id = data.get("driver_id")
    token = data.get("token")
    
    # if the driver is authorized
    if is_authorized(driver_id, token):
        mqtt_message = f"car closed by authorized driver {driver_id}"
        mqtt_client.publish(TOPICS["KEYLESS_ACCEPTED"], mqtt_message)
        return web.Response(text="Vehicle locked")
    else:
        add_attempts(driver_id, token)
        mqtt_message = f"{driver_id} is unauthorized"
        mqtt_client.publish(TOPICS["KEYLESS_ERROR"], mqtt_message)
        return web.Response(status=401, text="Unauthorized")

# Handler to fetch all drivers (for testing)
async def fetch_drivers_handler(request):
    drivers = fetch_drivers()
    return web.json_response({"drivers": drivers})

# Handler to fetch latest entry attempt
async def fetch_entry_attempts_handler(request):
    drivers = latest_attempt()
    driver_id = drivers[1]
    mqtt_message = f"latest driver: {driver_id}"
    mqtt_client.publish(TOPICS["KEYLESS_ACCEPTED"], mqtt_message)
    return web.json_response({"drivers": drivers})

# Handler to add a new driver
async def add_driver_handler(request):
    data = await request.json()
    driver_id = data.get("driver_id")
    token = data.get("token")

    if not driver_id or not token:
        return web.Response(status=400, text="Driver ID and token are required.")

    add_driver(driver_id, token)
    mqtt_client.publish(TOPICS["KEYLESS_ACCEPTED"], f"New driver {driver_id} added")

    return web.Response(text=f"Driver {driver_id} added successfully.")

# app routes
app = web.Application()
app.router.add_post("/keyless", keyless_handler)  # Keyless entry endpoint
app.router.add_post("/keyless_close", keyless_close_handler)
app.router.add_post("/add_driver", add_driver_handler)  # Add new driver endpoint
app.router.add_get("/drivers", fetch_drivers_handler)  # Fetch all drivers endpoint
app.router.add_get("/driver", fetch_entry_attempts_handler)  # Fetch all drivers endpoint

if __name__ == "__main__":
    initialize_db()
    entry_attempts()
    mqtt_client.loop_start()
    web.run_app(app, port=8081)
