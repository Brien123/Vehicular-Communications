import asyncio
from aiohttp import web
import sqlite3
import paho.mqtt.client as mqtt
from config.settings import MQTT_BROKER, TOPICS

# Initializing MQTT client
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    # Subscribe to relevant topics if needed
    # client.subscribe(TOPICS["KEYLESS_ACCEPTED"])

def on_message(client, userdata, msg):
    print(f"Message received: {msg.topic} - {msg.payload.decode()}")

mqtt_client = mqtt.Client()

# callbacks for connection and messages
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect(MQTT_BROKER)

# Initialize or create the SQLite database and table
def initialize_db():
    connection = sqlite3.connect('authorized_drivers.db')
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
    connection = sqlite3.connect('authorized_drivers.db')
    cursor = connection.cursor()
    cursor.execute("INSERT OR REPLACE INTO drivers (driver_id, token) VALUES (?, ?)", (driver_id, token))
    connection.commit()
    connection.close()
    print(f"Driver {driver_id} added to the database.")

# Function to fetch all drivers from the database
def fetch_drivers():
    connection = sqlite3.connect('authorized_drivers.db')
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM drivers")
    drivers = cursor.fetchall()
    connection.close()
    return drivers

# Function to check if the driver is authorized
def is_authorized(driver_id, token):
    connection = sqlite3.connect('authorized_drivers.db')
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

    # Check if the driver is authorized
    if is_authorized(driver_id, token):
        last_driver = driver_id
        mqtt_client.publish(TOPICS["KEYLESS_ACCEPTED"], f"{driver_id} authorized")
        return web.Response(text="Vehicle Unlocked")
    else:
        mqtt_client.publish(TOPICS["KEYLESS_ERROR"], "Unauthorized attempt")
        return web.Response(status=401, text="Unauthorized")

# Handler to fetch all drivers (for testing)
async def fetch_drivers_handler(request):
    drivers = fetch_drivers()
    return web.json_response({"drivers": drivers})

# Handler to add a new driver
async def add_driver_handler(request):
    data = await request.json()
    driver_id = data.get("driver_id")
    token = data.get("token")

    # Validate input data
    if not driver_id or not token:
        return web.Response(status=400, text="Driver ID and token are required.")

    # Add driver to the database
    add_driver(driver_id, token)

    # Publish MQTT message about the new driver added
    mqtt_client.publish(TOPICS["KEYLESS_ACCEPTED"], f"New driver {driver_id} added")

    return web.Response(text=f"Driver {driver_id} added successfully.")

# app routes
app = web.Application()
app.router.add_post("/keyless", keyless_handler)  # Keyless entry endpoint
app.router.add_post("/add_driver", add_driver_handler)  # Add new driver endpoint
app.router.add_get("/drivers", fetch_drivers_handler)  # Fetch all drivers endpoint

# Run the app
if __name__ == "__main__":
    initialize_db()  # Initialize the database when starting the server
    mqtt_client.loop_start()  # Start MQTT client loop
    web.run_app(app, port=8081)
