#!/usr/bin/env python3
"""
WerTigo Trip Planner - Backend Server Startup Script
"""

import os
import sys
from app import app, init_recommendation_engine

def main():
    """Main function to run the server"""
    print("=" * 60)
    print("🌟 WerTigo Trip Planner - Backend Server")
    print("=" * 60)
    
    # Initialize the recommendation engine
    print("📊 Initializing AI recommendation engine...")
    try:
        init_recommendation_engine()
        print("✅ Recommendation engine initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize recommendation engine: {e}")
        print("⚠️  Server will start but recommendations may not work properly.")
    
    # Server configuration
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print(f"\n🚀 Starting server on http://{host}:{port}")
    print(f"🔧 Debug mode: {'ON' if debug else 'OFF'}")
    print("\n📡 Available endpoints:")
    print("   • GET  /api/health          - Health check")
    print("   • POST /api/create-session  - Create session")
    print("   • POST /api/recommend       - Get recommendations")
    print("   • GET  /api/cities          - Get available cities")
    print("   • GET  /api/categories      - Get available categories")
    print("   • GET  /api/geocode         - Geocode locations")
    print("   • POST /api/trips           - Trip management")
    print("   • POST /api/route           - Route calculation")
    print("\n💡 Frontend should connect to: http://localhost:5000")
    print("=" * 60)
    
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 