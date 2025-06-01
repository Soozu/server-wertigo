# Wertigo Neural Model Integration

This document describes how to use the Wertigo neural recommendation model in your frontend applications.

## Overview

The Wertigo neural model is a deep learning model built with PyTorch and Hugging Face's Transformers library. It uses a RoBERTa-based architecture to understand user queries and recommend travel destinations in the Philippines.

## Setup

1. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Make sure the dataset file is available at `dataset/final_dataset.csv`

3. (Optional) If you have a pre-trained model, place it at `models/destination_recommender.pt`

## Usage Options

### 1. Web-based Chat Interface

The easiest way to interact with the model is through the built-in chat interface:

1. Start the server:

   ```bash
   python app.py
   ```

2. Open your browser and navigate to:

   ```
   http://localhost:5000/chat
   ```

3. Type your travel queries in the chat box

### 2. Command-line Testing

For testing and debugging, you can use the command-line interface:

```bash
# Interactive mode
python test_model.py --interactive

# Single query mode
python test_model.py --query "Show me beaches in Boracay"

# With filters
python test_model.py --query "Show me good places to visit" --city "Manila" --category "Museum"
```

### 3. API Integration

To integrate the model with your own frontend, use the following API endpoints:

#### Check Model Status

```
GET /api/model/status
```

Response:
```json
{
  "model_loaded": true,
  "embedding_shape": [1500, 768],
  "tokenizer_ready": true,
  "labels_count": 25
}
```

#### Get Sample Messages

```
GET /api/model/sample-messages
```

Response:
```json
{
  "success": true,
  "sample_messages": [
    "I want to visit Boracay for a beach vacation",
    "Show me historical sites in Manila",
    ...
  ]
}
```

#### Chat with Model

```
POST /api/model/chat
Content-Type: application/json

{
  "query": "I want to visit beaches in Boracay",
  "city": "Boracay",  // Optional
  "category": "Beach",  // Optional
  "budget": "luxury",  // Optional
  "budget_amount": 5000,  // Optional
  "limit": 5  // Optional
}
```

Response:
```json
{
  "success": true,
  "query": "I want to visit beaches in Boracay",
  "detected_city": "Boracay",
  "detected_category": "Beach",
  "detected_budget": null,
  "detected_budget_amount": null,
  "recommendations": [
    {
      "id": 123,
      "name": "White Beach",
      "city": "Boracay",
      "province": "Aklan",
      "description": "Beautiful white sand beach...",
      "category": "Beach",
      "ratings": 4.8,
      "budget": 0,
      "score": 0.92,
      "latitude": 11.9804,
      "longitude": 121.9189
    },
    ...
  ]
}
```

## Frontend Integration Example

Here's a simple example of how to integrate the model with a React application:

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function TravelChat() {
  const [query, setQuery] = useState('');
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await axios.post('/api/model/chat', { query });
      if (response.data.success) {
        setRecommendations(response.data.recommendations);
      }
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Where would you like to travel?"
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>
      
      <div className="recommendations">
        {recommendations.map((rec) => (
          <div key={rec.id} className="recommendation-card">
            <h3>{rec.name}</h3>
            <p>Location: {rec.city}, {rec.province}</p>
            <p>Category: {rec.category}</p>
            <p>Rating: {rec.ratings}/5</p>
            <p>{rec.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default TravelChat;
```

## Customization

You can customize the model's behavior by:

1. **Updating the dataset**: The model uses the data in `dataset/final_dataset.csv` for its recommendations
2. **Fine-tuning**: Train the model on additional data to improve its performance
3. **Modifying the query extraction**: Adjust the logic in `extract_query_info()` to better detect locations, categories, etc.

## Troubleshooting

If you encounter issues:

1. Check that all dependencies are installed
2. Ensure the dataset is properly formatted
3. Make sure you have enough memory for model initialization (at least 4GB RAM recommended)
4. Check the server logs for specific error messages

If the model is too slow, consider reducing the batch size or using a smaller model variant. 