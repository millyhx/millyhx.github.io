import sqlite3

# Connect to your SQLite database
conn = sqlite3.connect('my_app_db.sqlite')
cursor = conn.cursor()

# Check the schema of the pins table
cursor.execute("PRAGMA table_info(pins);")
columns = cursor.fetchall()

for column in columns:
    print(column)

# Close the connection
conn.close()
