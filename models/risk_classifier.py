import pickle, os
MODEL_PATH = os.path.join(os.path.dirname(__file__), "risk_model.pkl")

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

risk_map = {0: "Low", 1: "Medium", 2: "High"}

def classify_risk(temple_id, crowd, wait_time):
    return risk_map[int(model.predict([[temple_id, crowd, wait_time]])[0])]
