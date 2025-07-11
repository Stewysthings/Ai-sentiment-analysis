import React, { useState } from 'react';
import axios from 'axios';

const SentimentAnalyzer: React.FC = () => {
  const [text, setText] = useState('');
  const [result, setResult] = useState<{ sentiment?: string; confidence?: number; error?: string } | null>(null);

  const analyzeSentiment = async () => {
    try {
      const response = await axios.post('http://localhost:5000/predict', { text }, {
        headers: { 'X-API-KEY': 'your-secret-key-123', 'Content-Type': 'application/json' },
      });
      setResult(response.data);
    } catch (error) {
      console.error('Error analyzing sentiment:', error);
      setResult({ error: 'Failed to analyze sentiment' });
    }
  };

  return (
    <div>
      <h1>Sentiment Analyzer</h1>
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Enter text to analyze"
      />
      <button onClick={analyzeSentiment}>Analyze</button>
      {result && (
        <div>
          <h2>Result:</h2>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default SentimentAnalyzer;