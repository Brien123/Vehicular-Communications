import sqlite3

def fetch_drivers():
    connection = sqlite3.connect('authorized_drivers.db')
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM drivers")
    drivers = cursor.fetchall()
    connection.close()
    return drivers

# Fetch and print drivers
drivers = fetch_drivers()
print(drivers)
