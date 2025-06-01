from flask import Blueprint, request, jsonify
import logging
import sys
import os
import json
from datetime import datetime

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import execute_query
from middleware import login_required

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Blueprint for trips routes
trips_bp = Blueprint('trips', __name__)

@trips_bp.route('/', methods=['GET'])
@login_required
def get_user_trips(user_id, username, email):
    """Get all trips for the authenticated user"""
    try:
        trips = execute_query(
            """
            SELECT id, trip_name, destination, start_date, end_date, 
                   budget, travelers, created_at, updated_at
            FROM saved_trips
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
        
        # Convert dates to string format for JSON serialization
        for trip in trips:
            if trip.get('start_date'):
                trip['start_date'] = trip['start_date'].isoformat()
            if trip.get('end_date'):
                trip['end_date'] = trip['end_date'].isoformat()
            if trip.get('created_at'):
                trip['created_at'] = trip['created_at'].isoformat()
            if trip.get('updated_at'):
                trip['updated_at'] = trip['updated_at'].isoformat()
        
        return jsonify({
            "success": True,
            "trips": trips,
            "count": len(trips)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user trips: {e}")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500

@trips_bp.route('/', methods=['POST'])
@login_required
def create_trip(user_id, username, email):
    """Create a new trip for the authenticated user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "Invalid request data"
            }), 400
        
        # Required fields
        trip_name = data.get('trip_name')
        
        if not trip_name:
            return jsonify({
                "success": False,
                "message": "Trip name is required"
            }), 400
        
        # Optional fields
        destination = data.get('destination')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        budget = data.get('budget')
        travelers = data.get('travelers', 1)
        
        # Store additional data as JSON
        trip_data = data.get('trip_data')
        if trip_data:
            trip_data = json.dumps(trip_data)
        else:
            trip_data = None
        
        # Insert the trip
        trip_id = execute_query(
            """
            INSERT INTO saved_trips (
                user_id, trip_name, destination, start_date, end_date, 
                budget, travelers, trip_data
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, trip_name, destination, start_date, end_date, 
             budget, travelers, trip_data),
            fetch=False
        )
        
        if trip_id:
            return jsonify({
                "success": True,
                "message": "Trip created successfully",
                "trip_id": trip_id
            }), 201
        else:
            return jsonify({
                "success": False,
                "message": "Failed to create trip"
            }), 500
            
    except Exception as e:
        logger.error(f"Error creating trip: {e}")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500

@trips_bp.route('/<int:trip_id>', methods=['GET'])
@login_required
def get_trip(trip_id, user_id, username, email):
    """Get a specific trip by ID"""
    try:
        # Make sure the trip belongs to the authenticated user
        trip = execute_query(
            """
            SELECT id, trip_name, destination, start_date, end_date, 
                  budget, travelers, trip_data, created_at, updated_at
            FROM saved_trips
            WHERE id = %s AND user_id = %s
            """,
            (trip_id, user_id)
        )
        
        if not trip:
            return jsonify({
                "success": False,
                "message": "Trip not found or access denied"
            }), 404
        
        trip = trip[0]  # Get the first (and only) trip
        
        # Convert dates to string format for JSON serialization
        if trip.get('start_date'):
            trip['start_date'] = trip['start_date'].isoformat()
        if trip.get('end_date'):
            trip['end_date'] = trip['end_date'].isoformat()
        if trip.get('created_at'):
            trip['created_at'] = trip['created_at'].isoformat()
        if trip.get('updated_at'):
            trip['updated_at'] = trip['updated_at'].isoformat()
        
        # Parse JSON trip data if present
        if trip.get('trip_data'):
            try:
                trip['trip_data'] = json.loads(trip['trip_data'])
            except:
                pass  # Keep as string if parsing fails
        
        return jsonify({
            "success": True,
            "trip": trip
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting trip: {e}")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500

@trips_bp.route('/<int:trip_id>', methods=['PUT'])
@login_required
def update_trip(trip_id, user_id, username, email):
    """Update a specific trip by ID"""
    try:
        # First check if the trip exists and belongs to the user
        trip_check = execute_query(
            "SELECT id FROM saved_trips WHERE id = %s AND user_id = %s",
            (trip_id, user_id)
        )
        
        if not trip_check:
            return jsonify({
                "success": False,
                "message": "Trip not found or access denied"
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "Invalid request data"
            }), 400
        
        # Build the update query dynamically based on provided data
        updates = []
        params = []
        
        if 'trip_name' in data:
            updates.append("trip_name = %s")
            params.append(data['trip_name'])
        
        if 'destination' in data:
            updates.append("destination = %s")
            params.append(data['destination'])
        
        if 'start_date' in data:
            updates.append("start_date = %s")
            params.append(data['start_date'])
        
        if 'end_date' in data:
            updates.append("end_date = %s")
            params.append(data['end_date'])
        
        if 'budget' in data:
            updates.append("budget = %s")
            params.append(data['budget'])
        
        if 'travelers' in data:
            updates.append("travelers = %s")
            params.append(data['travelers'])
        
        if 'trip_data' in data:
            updates.append("trip_data = %s")
            params.append(json.dumps(data['trip_data']))
        
        if not updates:
            return jsonify({
                "success": False,
                "message": "No update data provided"
            }), 400
        
        # Add trip_id and user_id to params
        params.append(trip_id)
        params.append(user_id)
        
        # Execute the update
        result = execute_query(
            f"""
            UPDATE saved_trips 
            SET {', '.join(updates)}
            WHERE id = %s AND user_id = %s
            """,
            params,
            fetch=False
        )
        
        if result is not None:
            return jsonify({
                "success": True,
                "message": "Trip updated successfully"
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Failed to update trip"
            }), 500
            
    except Exception as e:
        logger.error(f"Error updating trip: {e}")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500

@trips_bp.route('/<int:trip_id>', methods=['DELETE'])
@login_required
def delete_trip(trip_id, user_id, username, email):
    """Delete a specific trip by ID"""
    try:
        # First check if the trip exists and belongs to the user
        trip_check = execute_query(
            "SELECT id FROM saved_trips WHERE id = %s AND user_id = %s",
            (trip_id, user_id)
        )
        
        if not trip_check:
            return jsonify({
                "success": False,
                "message": "Trip not found or access denied"
            }), 404
        
        # Delete the trip
        result = execute_query(
            "DELETE FROM saved_trips WHERE id = %s AND user_id = %s",
            (trip_id, user_id),
            fetch=False
        )
        
        if result is not None:
            return jsonify({
                "success": True,
                "message": "Trip deleted successfully"
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Failed to delete trip"
            }), 500
            
    except Exception as e:
        logger.error(f"Error deleting trip: {e}")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500 