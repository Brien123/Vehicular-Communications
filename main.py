import subprocess
import threading
import paho.mqtt.client as mqtt
from config.settings import MQTT_BROKER, MQTT_PORT, TOPICS

# Define scripts for each OBU module
MODULES = [
    "keyless_obu/keyless.py",
    "toll_obu/toll.py",
    "infot_obu/infot.py",
    "hmi_obu/hmi.py",
]

# Subprocess management
processes = []

# MQTT Client Setup
mqtt_client = mqtt.Client()


def on_connect(client, userdata, flags, rc):
    print("Central OBU connected to MQTT broker.")
    for topic in TOPICS.values():
        client.subscribe(topic)
        print(f"Subscribed to topic: {topic}")


def on_message(client, userdata, message):
    print(f"Received message on {message.topic}: {message.payload.decode()}")
    # Add custom logic to handle unintended situations here
    if message.topic == TOPICS["KEYLESS_ERROR"]:
        print("⚠️ ALERT: Unauthorized keyless access attempt detected!")
    elif message.topic == TOPICS["TOLL_SYSTEM"]:
        print("🛣️ Toll gate accessed. Processing...") 


def run_mqtt_broker():
    """Launch the MQTT broker (Eclipse Mosquitto) as a subprocess."""
    broker_process = subprocess.Popen(["mosquitto", "-v"])
    return broker_process


def run_modules():
    """Launch all OBU modules as subprocesses."""
    global processes
    processes = [subprocess.Popen(["python", module]) for module in MODULES]


def monitor_subprocesses():
    """Monitor subprocesses and restart any that fail."""
    while True:
        for i, process in enumerate(processes):
            if process.poll() is not None:  # Process has exited
                print(f"⚠️ Module {MODULES[i]} stopped unexpectedly. Restarting...")
                processes[i] = subprocess.Popen(["python", MODULES[i]])


if _name_ == "_main_":
    try:
        # Start the MQTT broker
        print("Starting MQTT Broker...")
        broker_process = run_mqtt_broker()

        # Launch all modules
        print("Launching OBU modules...")
        run_modules()

        # Start MQTT client
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        threading.Thread(target=mqtt_client.loop_forever, daemon=True).start()

        # Monitor OBUs
        monitor_subprocesses()

    except KeyboardInterrupt:
        print("\nShutting down Central OBU...")
        for process in processes:
            process.terminate()
        broker_process.terminate()
        print("System stopped.")