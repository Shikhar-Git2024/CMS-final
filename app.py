from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
import requests
from flask import redirect, url_for
import sqlite3, os, pickle, datetime
import requests
import pandas as pd
import numpy as np
import pymysql
import bcrypt
from flask import session
from dotenv import load_dotenv
import random
import smtplib
from email.message import EmailMessage



# YOUR MODELS
from models.people_counter import count_people
from models.risk_classifier import classify_risk
from models.wait_time_predictor import predict_wait_time
from models.crowd_predictor import predict_crowd

app = Flask(__name__)

# Set a secret key for session management for authentication
app.secret_key = "sugam_secret"

db = pymysql.connect(
    host="localhost",
    user="root",
    password="root@123",
    database="sugam_darshan"
)

cursor = db.cursor()
# ---------------- ENV VARIABLES ----------------
load_dotenv()

MAIL_EMAIL = os.getenv("MAIL_EMAIL")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")


# ---------------- TEMPLE MAP DATA ----------------
TEMPLES = {
    "mahakaleshwar": {"lat": 23.1828, "lon": 75.7680},
    "sabarimala": {"lat": 9.4333, "lon": 77.0800},
    "kashi": {"lat": 25.3109, "lon": 83.0107},
    "tirupati": {"lat": 13.6833, "lon": 79.3474}
}

TAG_MAP = {
    "hospital": "amenity=hospital",
    "medical": "amenity=pharmacy",
    "hotel": "tourism=hotel",
    "parking": "amenity=parking",
    "restaurant": "amenity=restaurant",
    "railway": "railway=station",
    "metro": "railway=subway_entrance",
    "bus": "highway=bus_stop"
}

RADIUS = 10000
# ------------------------------------------------

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "static/output"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ---------------- BASIC PAGES ----------------
@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/role")
def role():
    return render_template("role.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/vision")
def vision():
    return render_template("vision.html")

@app.route("/motivation")
def motivation():
    return render_template("motivation.html")

@app.route("/contactus")
def contactus():
    return render_template("contactus.html")

# ---------------- DEVOTEE LOGIN ----------------
@app.route("/devotee-login", methods=["GET", "POST"])
def devotee_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cursor.execute("SELECT * FROM devotees WHERE username=%s", (username,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode(), user[6].encode()):
            session["devotee_id"] = user[0]
            return redirect(url_for("devdash"))
        else:
            return "Invalid username or password"

    return render_template("devotee_login.html")

# ---------------- ADMIN LOGIN ----------------
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login_page():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cursor.execute("SELECT * FROM admins WHERE username=%s", (username,))
        admin = cursor.fetchone()

        if admin and bcrypt.checkpw(password.encode(), admin[2].encode()):
            session["admin_id"] = admin[0]
            return redirect(url_for("admindash"))
        else:
            return "Invalid admin username or password"

    return render_template("admin_login.html")

# ---------------- DEVOTEE REGISTRATION ----------------
@app.route("/devotee-register", methods=["GET", "POST"])
def devotee_register():
    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        phone = request.form["phone"]
        age = request.form["age"]
        username = request.form["username"]
        password = request.form["password"]

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        sql = """INSERT INTO devotees
        (fullname, email, phone, age, username, password)
        VALUES (%s, %s, %s, %s, %s, %s)"""

        cursor.execute(sql, (fullname, email, phone, age, username, hashed_password))
        db.commit()

        return redirect(url_for("devotee_login"))

    return render_template("devotee_register.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))

@app.route("/devotee/temple/<int:temple_id>")
def temple_detail(temple_id):
    if "devotee_id" not in session:
        return redirect(url_for("devotee_login"))
    temples = {
        1: "Mahakaleshwar",
        2: "Kashi Vishwanath",
        3: "Sabarimala",
        4: "Tirupati Balaji"
    }
    return render_template(
        "devotee/temple_detail.html",
        temple_name=temples.get(temple_id, "Temple")
    )

# ---------------- SEND OTP EMAIL ----------------
def send_otp_email(to_email, otp):
    msg = EmailMessage()
    msg.set_content(f"Your OTP for Sugam Darshan password reset is: {otp}")
    msg["Subject"] = "Sugam Darshan OTP"
    msg["From"] = MAIL_EMAIL
    msg["To"] = to_email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(MAIL_EMAIL, MAIL_PASSWORD)
    server.send_message(msg)
    server.quit()

# ---------------- FORGOT PASSWORD ----------------
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]

        cursor.execute("SELECT id FROM devotees WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user:
            otp = str(random.randint(100000, 999999))
            cursor.execute("UPDATE devotees SET otp=%s WHERE email=%s", (otp, email))
            db.commit()

            send_otp_email(email, otp)
            return redirect(url_for("verify_otp", email=email))
        else:
            error = "Email not found"

    return render_template("forgot_password.html")

# ---------------- VERIFY OTP ----------------
@app.route("/verify-otp/<email>", methods=["GET", "POST"])
def verify_otp(email):
    error = None

    if request.method == "POST":
        otp = request.form["otp"]

        cursor.execute("SELECT otp FROM devotees WHERE email=%s", (email,))
        real_otp = cursor.fetchone()

        if real_otp and otp == real_otp[0]:
            return redirect(url_for("reset_password", email=email))
        else:
            error = "Invalid OTP"

    return render_template("verify_otp.html", email=email, error=error)

# ---------------- RESET PASSWORD ----------------
@app.route("/reset-password/<email>", methods=["GET", "POST"])
def reset_password(email):
    if request.method == "POST":
        new_password = request.form["password"]

        hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())

        cursor.execute(
            "UPDATE devotees SET password=%s, otp=NULL WHERE email=%s",
            (hashed, email)
        )
        db.commit()

        return redirect(url_for("devotee_login"))

    return render_template("reset_password.html", email=email)

# DEVOTEE DASHBOARD
@app.route("/devotee")
def devdash():
    if "devotee_id" not in session:
        return redirect(url_for("devotee_login"))
    return render_template("devotee/devdash.html")

# --------------------- DEVOTEE PROFILE ----------------
@app.route("/devotee/profile")
def devotee_profile():
    if "devotee_id" not in session:
        return redirect(url_for("devotee_login"))

    devotee_id = session["devotee_id"]

    cursor.execute(
        "SELECT fullname, email, phone, age, username FROM devotees WHERE id=%s",
        (devotee_id,)
    )
    user = cursor.fetchone()

    return render_template("devotee/profile.html", user=user)

# --------------------- EDIT DEVOTEE PROFILE ----------------
@app.route("/devotee/profile/edit", methods=["GET", "POST"])
def edit_profile():
    if "devotee_id" not in session:
        return redirect(url_for("devotee_login"))

    devotee_id = session["devotee_id"]

    if request.method == "POST":
        fullname = request.form["fullname"]
        phone = request.form["phone"]
        age = request.form["age"]

        cursor.execute("""
            UPDATE devotees 
            SET fullname=%s, phone=%s, age=%s 
            WHERE id=%s
        """, (fullname, phone, age, devotee_id))
        db.commit()

        return redirect(url_for("devotee_profile"))

    cursor.execute("SELECT fullname, phone, age FROM devotees WHERE id=%s", (devotee_id,))
    user = cursor.fetchone()

    return render_template("devotee/edit_profile.html", user=user)

# --------------------- DELETE DEVOTEE ACCOUNT ----------------
@app.route("/devotee/delete", methods=["POST"])
def delete_account():
    if "devotee_id" not in session:
        return redirect(url_for("devotee_login"))

    devotee_id = session["devotee_id"]

    cursor.execute("DELETE FROM devotees WHERE id=%s", (devotee_id,))
    db.commit()

    session.clear()
    return redirect(url_for("landing"))

@app.route("/devotee/map")
def devmap():
    if "devotee_id" not in session:
        return redirect(url_for("devotee_login"))
    return render_template("devotee/map.html")


@app.route("/devotee/emergency")
def devemergency():
    if "devotee_id" not in session:
        return redirect(url_for("devotee_login"))
    return render_template("devotee/emergency.html")

@app.route("/devotee/planner")
def devplanner():
    if "devotee_id" not in session:
        return redirect(url_for("devotee_login"))
    return render_template("devotee/planner.html")

@app.route("/devotee/planner/result", methods=["POST"])
def planner_result():
    temple_id = request.form.get("temple")
    month = request.form.get("month")

    # call your ML model
    result = predict_crowd(
        temple_id=temple_id,
        month=month,
        day=None,
        hour=None
    )

    return jsonify(result)

@app.route("/devotee/temple/tirupati")
def tirupati():
    if "devotee_id" not in session:
        return redirect(url_for("devotee_login"))
    return render_template("devotee/temple/tirupati.html")

@app.route("/devotee/temple/kashi")
def kashi():
    if "devotee_id" not in session:
        return redirect(url_for("devotee_login"))
    return render_template("devotee/temple/kashi.html")

@app.route("/devotee/temple/sabarimala")
def sabarimala():
    if "devotee_id" not in session:
        return redirect(url_for("devotee_login"))
    return render_template("devotee/temple/sabarimala.html")

@app.route("/devotee/temple/mahakaleshwar")
def mahakaleshwar():
    if "devotee_id" not in session:
        return redirect(url_for("devotee_login"))
    return render_template("devotee/temple/mahakaleshwar.html")

@app.route("/test-db")
def test_db():
    cursor.execute("SELECT * FROM admins")
    data = cursor.fetchall()
    return str(data)


# ADMIN DASHBOARD
@app.route("/admin")
def admindash():
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))
    return render_template("admin/admindash.html")

# ---------------- ADMIN VIEW DEVOTEES ----------------
@app.route("/admin/devotees")
def admin_view_devotees():
    if "admin_id" not in session:
        return redirect(url_for("admin_login_page"))

    cursor.execute("SELECT id, fullname, email, phone, age, username FROM devotees")
    devotees = cursor.fetchall()

    return render_template("admin/devotees.html", devotees=devotees)

# ---------------- ML LOGIC ----------------
@app.route("/predict", methods=["POST"])
def predict():

    file = request.files["video"]
    temple_id = request.form["temple_id"]

    filename = secure_filename(file.filename)
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    output_path = os.path.join(OUTPUT_FOLDER, "processed_" + filename)

    file.save(input_path)

    # 1. YOLO People Counting
    crowd_count = count_people(input_path, output_path)

    # 2. ML Predictions
    predicted_crowd = predict_crowd(temple_id)
    wait_time = predict_wait_time(temple_id, crowd_count)
    risk = classify_risk(temple_id, crowd_count, wait_time)

    return jsonify({
        "crowd_count": crowd_count,
        "predicted_crowd": predicted_crowd,
        "wait_time": wait_time,
        "risk": risk,
        "video_path": output_path
    })

# ---------------- MAP API ----------------
@app.route("/temple-places")
def temple_places():
    temple = request.args.get("temple")
    lat = TEMPLES[temple]["lat"]
    lon = TEMPLES[temple]["lon"]

    results = []

    for key in TAG_MAP:
        query = f"""
        [out:json];
        node(around:{RADIUS},{lat},{lon})[{TAG_MAP[key]}];
        out;
        """
        url = "https://overpass-api.de/api/interpreter"
        res = requests.post(url, data=query).json()

        for el in res["elements"]:
            el["category"] = key
            results.append(el)

    return jsonify(results)

#---------------- WEATHER API ----------------
WEATHER_API_KEY = "2e082d3357d82349e6bf5659778d1cdd" 
TEMPLE_CITY = { "tirupati": "Tirupati", "kashi": "Varanasi", "sabarimala": "Pathanamthitta", "mahakaleshwar": "Ujjain" }
@app.route("/api/weather/<temple>")
def weather_api(temple):
    if temple not in TEMPLE_CITY:
        return jsonify({"error": "Invalid temple"}), 404

    city = TEMPLE_CITY[temple]
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"

    r = requests.get(url)
    data = r.json()

    print("RAW WEATHER:", data)  # VERY IMPORTANT

    if "weather" not in data:
        return jsonify({"error": data}), 500

    return jsonify({
        "desc": data["weather"][0]["description"],
        "temp": data["main"]["temp"],
        "humidity": data["main"]["humidity"]
    })


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
