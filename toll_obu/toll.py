from aiohttp import web
from config.settings import MQTT_BROKER, TOPICS, VIN
import paho.mqtt.client as mqtt

mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER)

toll_data = []

async def toll_awake_handler(request):
    gate_id = request.match_info['gate_id']
    toll_data.append(gate_id)
    mqtt_client.publish(TOPICS["TOLL_SYSTEM"], f"Gate {gate_id} accessed")
    return web.Response(text=VIN)

app = web.Application()
app.router.add_get("/toll-awake/{gate_id}", toll_awake_handler)

if _name_ == "_main_":
    web.run_app(app, port=8082)