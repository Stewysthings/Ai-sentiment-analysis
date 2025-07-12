import os
import sys
import json
from pathlib import Path

# Add the parent directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from transformers import pipeline

# Load the sentiment analysis pipeline
model_path = os.path.join(Config.MODEL_PATH, "distilbert")
try:
    if os.path.exists(model_path):
        sentiment_analyzer = pipeline("sentiment-analysis", model=model_path)
    else:
        print(f"Model not found at {model_path}, downloading...")
        sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
        sentiment_analyzer.save_pretrained(model_path)
        print(f"Model saved to {model_path}")
except Exception as e:
    print(f"Error loading model: {e}")
    exit(1)

def analyze_batch(input_file: str, output_file: str):
    """Analyze a batch of text from input_file and save results to output_file."""
    texts = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        if isinstance(data, dict) and 'text' in data:
                            texts.append(data['text'])
                        else:
                            print(f"Skipping invalid line: {line}")
                    except json.JSONDecodeError as e:
                        print(f"Error decoding line: {line} - {e}")
    except FileNotFoundError:
        print(f"Input file {input_file} not found. Please create it with valid JSONL format.")
        return

    # Analyze sentiments
    results = []
    for text in texts:
        result = sentiment_analyzer(text)[0]
        sentiment = result['label'].lower().replace("positive", "1").replace("negative", "0")
        confidence = result['score']
        results.append({
            "text": text,
            "sentiment": sentiment,
            "confidence": confidence,
            "model_version": "distilbert",
            "status": "success"
        })

    # Save results
    Path("output").mkdir(exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    input_file = "data/input.jsonl"
    output_file = "output/results.json"
    analyze_batch(input_file, output_file)
    print(f"Batch analysis complete. Results saved to {output_file}")