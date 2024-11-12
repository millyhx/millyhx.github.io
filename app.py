from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime
from geopy.geocoders import Nominatim
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Setup geolocator for location conversion
geolocator = Nominatim(user_agent="trackMyTravel")

# Ensure the directory exists before saving the file
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    conn = sqlite3.connect('my_app_db.sqlite')
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form["password"]
        if password == "admin":
            session["user_type"] = "admin"
        elif password == "user":
            session["user_type"] = "user"
        else:
            return "Invalid password!"
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/index", methods=["GET", "POST"])
def index():
    if "user_type" not in session:
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    cursor = conn.cursor()

    selected_pin_id = request.args.get("selected_pin_id", None)

    # Fetch all pins ordered by timestamp
    cursor.execute("SELECT * FROM pins ORDER BY timestamp DESC")
    pins = cursor.fetchall()

    # Fetch the most recent pin
    recent_pin = pins[0] if pins else None
    
    # Define comments (default to empty list)
    comments = []

    pins = [dict(pin) for pin in pins]

    # Fetch comments for the selected pin if available
    if selected_pin_id:
        comments = conn.execute("SELECT * FROM comments WHERE pin_id = ?", (selected_pin_id,)).fetchall()

    conn.close()

    return render_template("index.html", 
                           user_type=session["user_type"], 
                           pins=pins, 
                           comments=comments, 
                           recent_pin=recent_pin, 
                           selected_pin_id=selected_pin_id)

@app.route("/add_pin", methods=["POST"])
def add_pin():
    if session.get("user_type") != "admin":
        return redirect(url_for("index"))
    
    location = request.form["location"]
    description = request.form["description"]
    image = request.files["image"]
    image_filename = None

    # Geocode the location to get latitude and longitude
    location_data = geolocator.geocode(location)
    if location_data is not None:
        latitude = location_data.latitude
        longitude = location_data.longitude
    else:
        return "Location not found", 404

    image_filename = None
    if image:
        image_filename = image.filename
        image_path = os.path.join(UPLOAD_FOLDER, image_filename)
        image.save(image_path)
        image_filename = f"uploads/{image_filename}"  # store relative path
    else:
        image_filename = None

    # Get the current date formatted as DD/MM/YYYY
    timestamp = datetime.now().strftime("%d/%m/%Y")

    # Insert pin data into the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO pins (location, description, image, latitude, longitude, timestamp) VALUES (?, ?, ?, ?, ?, ?)", 
        (location, description, image_filename, latitude, longitude, timestamp)
    )
    conn.commit()
    conn.close()
    
    return redirect(url_for("index"))

@app.route("/add_comment/<int:pin_id>", methods=["POST"])
def add_comment(pin_id):
    if session.get("user_type") != "user":
        return redirect(url_for("index"))

    name = request.form["name"]
    message = request.form["message"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO comments (name, message, pin_id) VALUES (?, ?, ?)", (name, message, pin_id))
    conn.commit()
    conn.close()

    return redirect(url_for("index", selected_pin_id=pin_id))

@app.route("/logout")
def logout():
    session.pop("user_type", None)
    return redirect(url_for("login"))

@app.route("/api/get_pin/<int:pin_id>", methods=["GET"])
def get_pin(pin_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, location, description, latitude, longitude FROM pins WHERE id = ?", (pin_id,))
    pin = cursor.fetchone()
    conn.close()
    if pin:
        return {
            "id": pin["id"],
            "location": pin["location"],
            "description": pin["description"],
            "latitude": pin["latitude"],
            "longitude": pin["longitude"]
        }
    return {"error": "Pin not found"}, 404

@app.route("/remove_pin/<int:pin_id>", methods=["POST"])
def remove_pin(pin_id):
    if session.get("user_type") != "admin":
        return redirect(url_for("index"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pins WHERE id = ?", (pin_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("index"))

@app.route("/remove_comment/<int:comment_id>", methods=["POST"])
def remove_comment(comment_id):
    if session.get("user_type") != "user":
        return redirect(url_for("index"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("index"))

@app.route("/api/get_comments/<int:pin_id>")
def get_comments(pin_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM comments WHERE pin_id = ?", (pin_id,))
    comments = cursor.fetchall()
    conn.close()
    return {'comments': [dict(comment) for comment in comments]}  # Convert to dicts for JSON serialization

@app.route("/edit_pin/<int:pin_id>", methods=["GET", "POST"])
def edit_pin(pin_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the pin from the database
    cursor.execute("SELECT * FROM pins WHERE id = ?", (pin_id,))
    pin = cursor.fetchone()

    if not pin:
        return "Pin not found", 404

    if request.method == "POST":
        location = request.form["location"]
        description = request.form["description"]
        image = request.files["image"]
        image_filename = pin['image']

        # Geocode the location to get latitude and longitude
        location_data = geolocator.geocode(location)
        if location_data is not None:
            latitude = location_data.latitude
            longitude = location_data.longitude
        else:
            return "Location not found", 404

        if image:
            image_filename = f"static/uploads/{datetime.now().strftime('%Y%m%d%H%M%S')}_{image.filename}"
            image.save(image_filename)

        # Update the pin in the database
        cursor.execute("UPDATE pins SET location = ?, description = ?, image = ?, latitude = ?, longitude =? WHERE id = ?",
                       (location, description, image_filename, latitude, longitude, pin_id))
        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    conn.close()
    return render_template("edit_pin.html", pin=pin)

if __name__ == "__main__":
    app.run(debug=True)
