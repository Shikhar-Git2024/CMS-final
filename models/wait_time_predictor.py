import pickle,os
MODEL_PATH = os.path.join(os.path.dirname(__file__), "wait_time_model.pkl")

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

def predict_wait_time(temple_id, crowd, counters=2):
    return int(model.predict([[temple_id, crowd, counters]])[0])
