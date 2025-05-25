# AI Sentiment Analysis API 🚀  
![Python](https://img.shields.io/badge/python-3.9%2B-blue)  
![License](https://img.shields.io/badge/license-MIT-green)  
![Project Board](https://img.shields.io/badge/board-active-success)  

Real-time text sentiment classification using LinearSVC (89% accuracy). Containerized with Docker for easy deployment.  

## 📌 Project Tracking  
[▶️ View Project Board](https://github.com/Stewysthings/Ai-sentiment-analysis/projects/1)  
*Track current tasks, enhancements, and bugs*  

## Features  
| Component       | Description                          | Status        |  
|-----------------|--------------------------------------|---------------|  
| Model Training  | LinearSVC pipeline (`train.py`)      | ✅ Production |  
| Flask API       | REST endpoint (`app.py`)             | ✅ Production |  
| Docker Support  | Containerization                     | ✅ Implemented|  

## Data Setup  
```bash
# Full dataset (1.6M rows)  
curl -o data/twitter_sentiment.csv [YOUR_DATA_URL]  

# Sample data (100 rows included)  
data/sample.csv  
