import asyncio
import aiohttp
from aiohttp import web
import paho.mqtt.client as mqtt
import json
from config.settings import MQTT_BROKER, TOPICS, on_connect

# Deejay radio station url
DEEJAY_STATION = "https://www.deejay.it/api/broadcast_airplay/?get=now"

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.connect(MQTT_BROKER)

# Function to parse the data from Deejay station API
def parse_song_info(api_data):
    try:
        if "result" in api_data:
            return {
                "station": "Deejay",
                "song": api_data["result"]["title"],
                "artist": api_data["result"]["artist"],
                "cover_url": api_data["result"]["coverUrl"]
            }
        else:
            return {"error": "Failed to parse Deejay data"}
    except Exception as e:
        return {"error": f"Failed to parse data: {str(e)}"}

# Function to fetch and parse current song information from Deejay station
async def fetch_current_song():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(DEEJAY_STATION) as response:
                if response.status == 200:
                    # Try to parse as JSON, if it returns text/plain, attempt to manually decode
                    try:
                        api_data = await response.json()
                    except Exception:
                        api_data = json.loads(await response.text())
                    return parse_song_info(api_data)
                else:
                    return {"error": f"Failed to fetch data (Status {response.status})"}
    except Exception as e:
        return {"error": str(e)}

async def publish_to_mqtt(song_info):
    if "error" in song_info:
        print("Error fetching song info:", song_info["error"])
        return

    # Prepare the message to send to MQTT
    # mqtt_message = json.dumps(song_info)
    mqtt_message = json.dumps({
        "station": song_info["station"],
        "song": song_info["song"],
        "artist": song_info["artist"]
    })
    mqtt_client.publish(TOPICS["RADIO"], mqtt_message)
    print(f"Published song info to MQTT: {mqtt_message}")

# Handler for fetching current song information from Deejay station
async def get_current_song_handler(request):
    song_info = await fetch_current_song()
    await publish_to_mqtt(song_info)

    return web.json_response(song_info)

# App initialization and routes
app = web.Application()
app.router.add_get("/current-song", get_current_song_handler)

if __name__ == "__main__":
    mqtt_client.loop_start()
    web.run_app(app, port=8083)
