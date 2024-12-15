import paho.mqtt.client as mqtt
from config.settings import MQTT_BROKER, TOPICS

def on_message(client, userdata, message):
    print(f"Topic: {message.topic} | Message: {message.payload.decode()}")

mqtt_client = mqtt.Client()
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER)

for topic in TOPICS.values():
    mqtt_client.subscribe(topic)

mqtt_client.loop_forever()