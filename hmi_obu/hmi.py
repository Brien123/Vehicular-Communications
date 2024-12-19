import paho.mqtt.client as mqtt
import json
from config.settings import TOPICS, MQTT_BROKER, MQTT_PORT
import time

# Global Variables
current_song_info = None
toll_event_info = None
keyless_status = None


# Called when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with result code {rc}")
    # Subscribe to topics
    client.subscribe(TOPICS["KEYLESS_ACCEPTED"])
    client.subscribe(TOPICS["KEYLESS_ERROR"])
    client.subscribe(TOPICS["TOLL_SYSTEM"])
    client.subscribe(TOPICS["RADIO"])

# Called when a message is received from the broker
def on_message(client, userdata, msg):
    global current_song_info, toll_event_info, keyless_status

    topic = msg.topic
    payload = msg.payload.decode("utf-8")

    if topic == TOPICS["KEYLESS_ACCEPTED"]:
        # print(f"Keyless Entry Accepted: {payload}")
        keyless_status = {"status": "accepted", "message": payload}
        display_keyless_status(keyless_status)

    elif topic == TOPICS["KEYLESS_ERROR"]:
        # print(f"Keyless Entry Error: {payload}")
        keyless_status = {"status": "error", "message": payload}
        display_keyless_status(keyless_status)

    elif topic == TOPICS["TOLL_SYSTEM"]:
        # print(f"Toll Event: {payload}")
        toll_event_info = {"event": payload}
        display_toll_event(toll_event_info)

    elif topic == TOPICS["RADIO"]:
        # print(f"Radio Information: {payload}")
        try:
            song_info = json.loads(payload)
            current_song_info = song_info
            display_radio_info(current_song_info)
        except json.JSONDecodeError:
            print("Error decoding song information")


# Function to display Keyless Entry Status
def display_keyless_status(status):
    if status["status"] == "accepted":
        print(f"Keyless Entry Accepted: {status['message']}")
    elif status["status"] == "error":
        print(f"Keyless Entry Error: {status['message']}")


# Function to display Toll Event
def display_toll_event(event_info):
    print(f"Toll Event: {event_info['event']}")


# Function to display Radio Info
def display_radio_info(song_info):
    print(f"Now Playing: {song_info['song']} by {song_info['artist']}")
    # print(f"Station: {song_info['station']}")
    # print(f"Cover Image: {song_info['cover_url']}")


# Set up MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Connect to the broker
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Start the MQTT client loop
mqtt_client.loop_start()

# Keep the script running indefinitely
try:
    while True:
        time.sleep(1)  # Keeps the script alive without doing anything
except KeyboardInterrupt:
    print("Script terminated.")
    mqtt_client.loop_stop()  # Stop the MQTT loop when you terminate the script
