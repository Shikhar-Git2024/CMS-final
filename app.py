from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
import requests
from flask import redirect, url_for


# YOUR MODELS
from models.people_counter import count_people
from models.risk_classifier import classify_risk
from models.wait_time_predictor import predict_wait_time
from models.crowd_predictor import predict_crowd

app = Flask(__name__)

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

# ---------------- LOGIN & REGISTER ----------------
@app.route("/devotee-login", methods=["GET", "POST"])
def devotee_login():
    if request.method == "POST":
        return redirect(url_for("devdash"))  # ✅ FIXED
    return render_template("devotee_login.html")

@app.route("/devotee-register", methods=["GET", "POST"])
def devotee_register():
    if request.method == "POST":
        return redirect(url_for("devdash"))
    return render_template("devotee_register.html")

@app.route("/devotee/temple/<int:temple_id>")
def temple_detail(temple_id):
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


# DEVOTEE DASHBOARD
@app.route("/devotee")
def devdash():
    return render_template("devotee/devdash.html")

@app.route("/devotee/map")
def devmap():
    return render_template("devotee/map.html")


@app.route("/devotee/emergency")
def devemergency():
    return render_template("devotee/emergency.html")

@app.route("/devotee/planner")
def devplanner():
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

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login_page():   # 👈 name changed
    if request.method == "POST":
        return redirect(url_for("admindash"))
    return render_template("admin_login.html")



# ADMIN DASHBOARD
@app.route("/admin")
def admindash():
    return render_template("admin/admindash.html")

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

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
