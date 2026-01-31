import pickle, datetime, os
MODEL_PATH = os.path.join(os.path.dirname(__file__), "temple_crowd_model.pkl")

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

def predict_crowd(temple_id):
    now = datetime.datetime.now()
    return int(model.predict([[temple_id, now.hour, now.weekday()]])[0])
