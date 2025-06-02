# WerTigo Python Backend

AI-powered recommendation engine and route calculation service for the WerTigo travel planner.

## Overview

This Python backend focuses on AI-powered features and computational services:

- 🤖 **AI Recommendations**: Machine learning-based destination recommendations
- 🗺️ **Geocoding**: Location name to coordinates conversion
- 🛣️ **Route Calculation**: Intelligent route planning between destinations
- 🧠 **Neural Model**: Advanced recommendation using RoBERTa embeddings

## Architecture

**Hybrid Backend Setup:**
- **Python Backend** (Port 5000): AI recommendations, geocoding, route calculation
- **Express Backend** (Port 3001): Authentication, tickets, reviews, trip sharing

## Features

### AI Recommendations
- TF-IDF based similarity matching
- Neural model with RoBERTa embeddings
- Context-aware query understanding
- Philippine destinations specialization

### Route Calculation
- OpenRouteService integration
- OSRM fallback routing
- Intelligent curve generation for island routes
- Philippine geography optimization

### Geocoding
- Nominatim OpenStreetMap integration
- Philippines-focused location search
- Coordinate conversion services

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/create-session` | Create user session |
| POST | `/api/recommend` | Get AI recommendations |
| GET | `/api/cities` | Available cities |
| GET | `/api/categories` | Available categories |
| GET | `/api/geocode` | Geocode locations |
| POST | `/api/route` | Calculate routes |
| POST | `/api/model/chat` | Neural model chat |
| GET | `/api/model/status` | Model status |

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up dataset:**
   ```bash
   # Ensure dataset/final_dataset.csv exists
   ```

3. **Run the server:**
   ```bash
   python run_server.py
   # or
   python app.py
   ```

## Dependencies

- Flask - Web framework
- pandas - Data manipulation
- scikit-learn - Machine learning
- torch - Neural networks
- transformers - RoBERTa model
- requests - HTTP client

## Integration

The Python backend works alongside the Express.js backend:

```javascript
// Frontend integration example
const PYTHON_API = 'http://localhost:5000/api';
const EXPRESS_API = 'http://localhost:3001/api';

// AI recommendations (Python)
const recommendations = await fetch(`${PYTHON_API}/recommend`, {
  method: 'POST',
  body: JSON.stringify({ query: 'beaches in Boracay' })
});

// Authentication (Express)
const auth = await fetch(`${EXPRESS_API}/auth/login`, {
  method: 'POST',
  body: JSON.stringify({ email, password })
});
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `5000` |
| `DEBUG` | Debug mode | `True` |

## Development

```bash
# Start in development mode
python run_server.py

# Check model status
curl http://localhost:5000/api/model/status

# Test recommendations
curl -X POST http://localhost:5000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"query": "beautiful beaches in Philippines"}'
```

## Migration Notes

**Removed from Python Backend:**
- ❌ Authentication routes (`/api/auth/*`)
- ❌ Ticket management (`/api/tickets/*`)
- ❌ Trip CRUD operations (`/api/trips/*`)
- ❌ Database connections and ORM
- ❌ User session management

**Kept in Python Backend:**
- ✅ AI recommendation engine
- ✅ Geocoding services
- ✅ Route calculation
- ✅ Neural model inference
- ✅ Philippine destinations data

This focused approach allows the Python backend to excel at AI and computational tasks while the Express backend handles data persistence and user management.

## 🚀 Features

- **AI-Powered Recommendations**: Uses TF-IDF and cosine similarity for intelligent destination matching
- **Session Management**: Secure session handling for user interactions
- **Trip Planning**: Create, manage, and update travel itineraries
- **Geocoding**: Location-to-coordinates conversion using OpenStreetMap
- **Route Calculation**: Basic route planning between destinations
- **Philippine Focus**: Specialized dataset covering destinations across Luzon, Visayas, and Mindanao

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## 🛠️ Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <your-repo-url>
   cd Wertigo/server
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify dataset is in place**:
   Make sure `dataset/final_dataset.csv` exists with your destination data.

## 🏃‍♂️ Running the Server

### Option 1: Using the startup script (recommended)
```bash
python run_server.py
```

### Option 2: Using Flask directly
```bash
python app.py
```

### Option 3: Using Gunicorn (production)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

The server will start on `http://localhost:5000`

## 📡 API Endpoints

### Health Check
```http
GET /api/health
```
Returns server status and model loading state.

### Session Management
```http
POST /api/create-session
GET /api/validate-session/{session_id}
```

### Recommendations
```http
POST /api/recommend
Content-Type: application/json

{
  "query": "beautiful beaches in Boracay",
  "limit": 5,
  "city": "Tagaytay",
  "category": "Restaurant", 
  "rating": 4.5
}
```

### Data Endpoints
```http
GET /api/cities        # Get available cities
GET /api/categories    # Get available categories
```

### Geocoding
```http
GET /api/geocode?q=Tagaytay,%20Cavite
```

### Trip Management
```http
POST /api/trips        # Create trip
GET /api/trips/{id}    # Get trip
PUT /api/trips/{id}    # Update trip
```

### Route Calculation
```http
POST /api/route
Content-Type: application/json

{
  "points": [
    {"lat": 14.1, "lng": 120.9, "name": "Start"},
    {"lat": 14.2, "lng": 121.0, "name": "End"}
  ]
}
```

## 🤖 How the AI Works

The recommendation engine uses:

1. **TF-IDF Vectorization**: Converts destination descriptions into numerical features
2. **Cosine Similarity**: Matches user queries with destination content
3. **Combined Scoring**: Weights similarity (70%) and ratings (30%) for final ranking
4. **Smart Filtering**: Detects cities, categories, and preferences from natural language
5. **Fallback Handling**: Provides suggestions when no exact matches are found

## 📊 Dataset Format

The CSV dataset should have these columns:
- `id`: Unique identifier
- `name`: Destination name
- `city`: City location
- `province`: Province location
- `description`: Detailed description
- `category`: Type of destination
- `ratings`: Rating (1-5)
- `budget`: Cost estimate
- `latitude`: GPS latitude
- `longitude`: GPS longitude
- `operating hours`: Operating hours
- `contact information`: Contact details

## 🔧 Configuration

### Environment Variables
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 5000)
- `DEBUG`: Debug mode (default: True)

### Frontend Configuration
Update `client/js/config.js`:
```javascript
const API_CONFIG = {
  BASE_URL: 'http://localhost:5000',  // Change for production
  // ... other settings
};
```

## 🐛 Troubleshooting

### Common Issues

1. **"Recommendation engine not available"**
   - Check if `dataset/final_dataset.csv` exists
   - Verify CSV format matches expected columns
   - Check server logs for specific errors

2. **CORS errors from frontend**
   - Ensure Flask-CORS is installed
   - Check that frontend is using correct API URL

3. **Import errors**
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version compatibility

4. **Geocoding not working**
   - Check internet connection
   - OpenStreetMap Nominatim service might be temporarily unavailable

### Debug Mode
Run with debug logging:
```bash
export DEBUG=True
python run_server.py
```

## 🚀 Deployment

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Use a production WSGI server (Gunicorn)
- [ ] Configure proper CORS settings
- [ ] Set up SSL/HTTPS
- [ ] Use a production database for trip storage
- [ ] Set up proper logging
- [ ] Configure environment variables

### Docker Deployment (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## 📝 API Response Examples

### Successful Recommendation
```json
{
  "recommendations": [
    {
      "id": 1,
      "name": "Sky Ranch Tagaytay",
      "city": "Tagaytay",
      "province": "Cavite",
      "description": "An amusement park with spectacular views...",
      "category": "Leisure",
      "rating": 4.3,
      "budget": 900,
      "latitude": 14.09543379,
      "longitude": 120.9377015,
      "operating_hours": "10:00 AM - 10:00 PM",
      "contact_information": "https://www.facebook.com/...",
      "similarity_score": 0.85
    }
  ],
  "detected_city": "Tagaytay",
  "detected_category": "Leisure",
  "total_found": 5,
  "is_conversation": false
}
```

### No Results Found
```json
{
  "is_conversation": true,
  "message": "I don't have that type of place in Manila, but I have other options!",
  "detected_city": "Manila",
  "available_categories": ["Restaurant", "Historical Site", "Museum"],
  "available_cities": ["Tagaytay", "Cavite", "Amadeo"]
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review server logs
3. Create an issue in the repository 