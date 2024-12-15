import asyncio
import aiohttp
from config.settings import MQTT_BROKER, TOPICS
import paho.mqtt.client as mqtt

mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER)

RADIO_API = "https://www.deejay.it/api/broadcast_airplay/?get=now"

async def fetch_radio_info():
    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get(RADIO_API) as response:
                if response.status == 200:
                    data = await response.json()
                    current_song = data.get('now', {}).get('title', 'Unknown')
                    mqtt_client.publish(TOPICS["RADIO"], f"Now playing: {current_song}")
            await asyncio.sleep(30)

if _name_ == "_main_":
    asyncio.run(fetch_radio_info())