import pandas as pd
from pathlib import Path

# Modified data loading - tries sample.csv first, falls back to full dataset
DATA_PATH = Path("data/sample.csv")  # Default to small sample
if not DATA_PATH.exists():
    DATA_PATH = Path("data/twitter_sentiment.csv")  # Fallback to full data
    
data = pd.read_csv(DATA_PATH)
print(f"Using dataset: {DATA_PATH} ({len(data)} rows)")