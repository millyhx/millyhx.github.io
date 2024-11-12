import sqlite3

# Connect to your SQLite database
conn = sqlite3.connect('my_app_db.sqlite')
cursor = conn.cursor()

# Add latitude and longitude columns


cursor.execute("ALTER TABLE pins ADD COLUMN timestamp TEXT;")


# Commit the changes and close the connection
conn.commit()
conn.close()

