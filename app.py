from flask import Flask, request, jsonify
import joblib
from pathlib import Path

app = Flask(__name__)

# Load models
model = joblib.load(Path("models/model.pkl"))
vectorizer = joblib.load(Path("models/vectorizer.pkl"))

@app.route("/predict", methods=["POST"])
def predict():
    text = request.json.get("text", "")
    features = vectorizer.transform([text])
    return jsonify({
        "sentiment": int(model.predict(features)[0]),
        "text": text
    })

if __name__ == "__main__":
    app.run(debug=True)
