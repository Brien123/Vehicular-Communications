# MQTT Broker configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# MQTT Topics
TOPICS = {
    "KEYLESS_ACCEPTED": "vc2425/keyless-accepted",
    "KEYLESS_ERROR": "vc2425/keyless-error",
    "TOLL_SYSTEM": "vc2425/toll-system",
    "RADIO": "vc2425/radio",
}

# Radio stations
RADIO_STATIONS = [
    "https://www.deejay.it/api/broadcast_airplay/?get=now",
    "https://api.broadcast.radio/api/nowplaying/8",
    "https://demo.azuracast.com/api/nowplaying",
    "https://radio.balearic-fm.com/api/nowplaying"
]

# vehicle Identification Number
VIN = "1HGBH41JXMN109186"

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")