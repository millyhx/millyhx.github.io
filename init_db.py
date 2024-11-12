import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('my_app_db.sqlite')
cursor = conn.cursor()

# Create tables for the app
cursor.execute('''
CREATE TABLE IF NOT EXISTS pins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location TEXT NOT NULL,
    description TEXT NOT NULL,
    image TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    message TEXT NOT NULL,
    pin_id INTEGER,
    FOREIGN KEY(pin_id) REFERENCES pins(id)
)
''')

conn.commit()
conn.close()
