import sqlite3
from datetime import datetime

from keyless_obu.keyless import add_attempts, latest_attempt

#
def fetch_entries():
    connection = sqlite3.connect('smart_vehicle.db')
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM entry_attempts")
    drivers = cursor.fetchall()
    connection.close()
    return drivers

# Fetch and print drivers
drivers = fetch_entries()
print(drivers)

connection = sqlite3.connect('smart_vehicle.db')
cursor = connection.cursor()

def add_attempts(driver_id, token, cursor):
    connection = sqlite3.connect('smart_vehicle.db')
    cursor = connection.cursor()
    created_at = datetime.now()
    try:
        result = cursor.execute(
            "INSERT OR REPLACE INTO entry_attempts (driver_id, token, created_at) VALUES (?, ?, ?)",
            (driver_id, token, created_at)
        )
        connection.close()
        print("attempt saved")
        return result
    except Exception as e:
        return f"error: {str(e)}"

add_attempts("zeh", "172828", cursor)

