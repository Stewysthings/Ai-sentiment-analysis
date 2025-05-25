import os
import re
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import (accuracy_score, classification_report, 
                            ConfusionMatrixDisplay)
from sklearn.model_selection import train_test_split
import joblib  # For model saving

# ======================
# CONFIGURATION
# ======================
OUTPUT_DIR = 'results'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ======================
# TEXT PROCESSING
# ======================
def clean_text(text):
    """Enhanced text cleaning with negation handling"""
    if not isinstance(text, str):
        return ""
    
    # Step 1: Remove URLs/mentions/hashtags
    text = re.sub(r'http\S+|@\w+|#\w+', '', text)
    
    # Step 2: Handle negations ("not good" → "not_good")
    text = re.sub(r"(not|no|never)\s+(\w+)", r"\1_\2", text)
    
    # Step 3: Keep only letters and basic punctuation
    text = re.sub(r'[^a-zA-Z.!?, ]', '', text)
    
    # Step 4: Convert to lowercase and remove short words
    words = [word.lower() for word in text.split() if len(word) > 2]
    
    return ' '.join(words)

# ======================
# MODEL TRAINING
# ======================
def train_model(X_train, y_train):
    """Train and return model with vectorizer"""
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),  # Capture word pairs
        stop_words=['the', 'and', 'is']  # Basic stopwords
    )
    
    model = LinearSVC(
        class_weight='balanced',
        max_iter=2000,
        random_state=42,
        verbose=1  # Show training progress
    )
    
    print("Vectorizing text...")
    X_train_vec = vectorizer.fit_transform(X_train)
    
    print("Training model...")
    model.fit(X_train_vec, y_train)
    
    return model, vectorizer

# ======================
# VISUALIZATION & SAVING
# ======================
def save_results(model, vectorizer, X_test, y_test, test_pred):
    """Save all outputs"""
    # 1. Save model artifacts
    joblib.dump(model, f'{OUTPUT_DIR}/model.pkl')
    joblib.dump(vectorizer, f'{OUTPUT_DIR}/vectorizer.pkl')
    
    # 2. Save misclassified examples
    errors = pd.DataFrame({
        'text': X_test,
        'actual': y_test,
        'predicted': test_pred
    }).query('actual != predicted').sample(10)
    
    errors.to_csv(f'{OUTPUT_DIR}/misclassified_samples.csv', index=False)
    
    # 3. Generate confusion matrix
    ConfusionMatrixDisplay.from_predictions(y_test, test_pred)
    plt.savefig(f'{OUTPUT_DIR}/confusion_matrix.png')
    plt.close()

# ======================
# MAIN EXECUTION
# ======================
def main():
    print("🚀 Starting production-ready sentiment analysis")
    
    try:
        # 1. Load data
        print("\n📂 Loading data...")
        df = pd.read_csv(
            "data/twitter_sentiment.csv",
            encoding='latin1',
            header=None,
            usecols=[0, 5],
            names=['sentiment', 'text']
        )
        df['sentiment'] = df['sentiment'].map({0: 0, 4: 1})
        print(f"✔ Loaded {len(df):,} tweets (0:Negative, 1:Positive)")
        
        # 2. Clean text
        print("\n🧹 Cleaning text...")
        df['clean_text'] = df['text'].apply(clean_text)
        
        # 3. Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            df['clean_text'], df['sentiment'],
            test_size=0.2,
            random_state=42,
            stratify=df['sentiment']
        )
        
        # 4. Train model
        print("\n🤖 Training model...")
        model, vectorizer = train_model(X_train, y_train)
        
        # 5. Evaluate
        print("\n📊 Evaluating model...")
        test_pred = model.predict(vectorizer.transform(X_test))
        
        print("\n" + "="*40)
        print(f"✅ Model Accuracy: {accuracy_score(y_test, test_pred):.1%}")
        print("="*40)
        print("\nDetailed Report:")
        print(classification_report(y_test, test_pred))
        
        # 6. Save outputs
        save_results(model, vectorizer, X_test, y_test, test_pred)
        print(f"\n💾 Saved results to '{OUTPUT_DIR}' folder:")
        print(f"- model.pkl : Trained model")
        print(f"- vectorizer.pkl : Text processor")
        print(f"- misclassified_samples.csv : Error analysis")
        print(f"- confusion_matrix.png : Visual report")
        
    except Exception as e:
        print(f"\n❌ Critical error: {str(e)}")
        return 1

if __name__ == "__main__":
    main()