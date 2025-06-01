import os
import mysql.connector
from mysql.connector import pooling
import logging
from dotenv import load_dotenv
import pathlib

# Load environment variables from .env file if it exists
env_path = pathlib.Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()  # Try to load from default location

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'wertigo_user'),
    'password': os.environ.get('DB_PASSWORD', 'wertigo_password'),
    'database': os.environ.get('DB_NAME', 'wertigo_db'),
    'port': int(os.environ.get('DB_PORT', '3306')),
}

# Connection pool
try:
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="wertigo_pool",
        pool_size=5,
        **DB_CONFIG
    )
    logger.info("Database connection pool created successfully")
except Exception as e:
    logger.error(f"Error creating database connection pool: {e}")
    connection_pool = None

def get_connection():
    """Get a connection from the pool"""
    try:
        if connection_pool:
            return connection_pool.get_connection()
        else:
            logger.error("Connection pool is not available")
            return None
    except Exception as e:
        logger.error(f"Error getting connection from pool: {e}")
        return None

def execute_query(query, params=None, fetch=True):
    """Execute a query and return results if any"""
    connection = get_connection()
    if not connection:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        result = None
        if fetch:
            result = cursor.fetchall()
        else:
            connection.commit()
            result = cursor.lastrowid
            
        return result
    except Exception as e:
        logger.error(f"Database error: {e}")
        connection.rollback()
        return None
    finally:
        if connection:
            cursor.close()
            connection.close()

def create_tables():
    """Create necessary tables if they don't exist"""
    # Users table
    users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        first_name VARCHAR(50),
        last_name VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );
    """
    
    # User sessions table
    sessions_table = """
    CREATE TABLE IF NOT EXISTS user_sessions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        session_id VARCHAR(255) UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """
    
    # Trips table - updated structure
    trips_table = """
    CREATE TABLE IF NOT EXISTS trips (
        id VARCHAR(36) PRIMARY KEY,
        user_id INT,
        session_id VARCHAR(255),
        trip_name VARCHAR(100),
        destination VARCHAR(100),
        start_date DATE,
        end_date DATE,
        budget DECIMAL(10, 2),
        travelers INT DEFAULT 1,
        status ENUM('active', 'completed', 'cancelled') DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
        INDEX idx_session_id (session_id),
        INDEX idx_user_id (user_id)
    );
    """
    
    # Trip destinations table
    trip_destinations_table = """
    CREATE TABLE IF NOT EXISTS trip_destinations (
        id INT AUTO_INCREMENT PRIMARY KEY,
        trip_id VARCHAR(36) NOT NULL,
        destination_id INT,
        name VARCHAR(255) NOT NULL,
        city VARCHAR(100),
        province VARCHAR(100),
        description TEXT,
        category VARCHAR(50),
        rating DECIMAL(3, 2),
        budget DECIMAL(10, 2),
        latitude DECIMAL(10, 8),
        longitude DECIMAL(11, 8),
        operating_hours VARCHAR(255),
        contact_information VARCHAR(255),
        order_index INT DEFAULT 0,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
        INDEX idx_trip_id (trip_id),
        INDEX idx_order (trip_id, order_index)
    );
    """
    
    # Trip routes table - for storing calculated routes
    trip_routes_table = """
    CREATE TABLE IF NOT EXISTS trip_routes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        trip_id VARCHAR(36) NOT NULL,
        route_data JSON,
        distance_km DECIMAL(8, 2),
        time_minutes INT,
        route_source VARCHAR(50),
        calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
        INDEX idx_trip_id (trip_id)
    );
    """
    
    # Saved trips table (legacy - keeping for backward compatibility)
    saved_trips_table = """
    CREATE TABLE IF NOT EXISTS saved_trips (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        trip_name VARCHAR(100) NOT NULL,
        destination VARCHAR(100),
        start_date DATE,
        end_date DATE,
        budget DECIMAL(10, 2),
        travelers INT DEFAULT 1,
        trip_data JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """
    
    # User preferences table
    preferences_table = """
    CREATE TABLE IF NOT EXISTS user_preferences (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        preference_key VARCHAR(50) NOT NULL,
        preference_value TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY user_preference (user_id, preference_key),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """
    
    # Generated ticket IDs table
    generated_tickets_table = """
    CREATE TABLE IF NOT EXISTS generated_tickets (
        id INT AUTO_INCREMENT PRIMARY KEY,
        ticket_id VARCHAR(50) UNIQUE NOT NULL,
        ticket_type ENUM('FLIGHT', 'BUS', 'FERRY', 'TRAIN', 'HOTEL', 'TOUR', 'BOOKING_REF', 'CONFIRMATION') NOT NULL,
        user_id INT,
        session_id VARCHAR(255),
        is_used BOOLEAN DEFAULT FALSE,
        used_at TIMESTAMP NULL,
        include_timestamp BOOLEAN DEFAULT TRUE,
        metadata JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
        INDEX idx_ticket_id (ticket_id),
        INDEX idx_user_id (user_id),
        INDEX idx_session_id (session_id),
        INDEX idx_ticket_type (ticket_type),
        INDEX idx_created_at (created_at)
    );
    """
    
    # Trip trackers table
    trip_trackers_table = """
    CREATE TABLE IF NOT EXISTS trip_trackers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        tracker_id VARCHAR(50) UNIQUE NOT NULL,
        trip_id VARCHAR(36) NOT NULL,
        email VARCHAR(255) NOT NULL,
        traveler_name VARCHAR(255),
        phone VARCHAR(50),
        is_active BOOLEAN DEFAULT TRUE,
        access_count INT DEFAULT 0,
        last_accessed TIMESTAMP NULL,
        expires_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
        INDEX idx_tracker_id (tracker_id),
        INDEX idx_trip_id (trip_id),
        INDEX idx_email (email),
        INDEX idx_created_at (created_at)
    );
    """
    
    execute_query(users_table, fetch=False)
    execute_query(sessions_table, fetch=False)
    execute_query(trips_table, fetch=False)
    execute_query(trip_destinations_table, fetch=False)
    execute_query(trip_routes_table, fetch=False)
    execute_query(saved_trips_table, fetch=False)
    execute_query(preferences_table, fetch=False)
    execute_query(generated_tickets_table, fetch=False)
    execute_query(trip_trackers_table, fetch=False)
    logger.info("Database tables created or verified")

# Trip Management Functions

def create_trip_db(trip_id, user_id=None, session_id=None, trip_data=None):
    """Create a new trip in the database"""
    try:
        query = """
        INSERT INTO trips (id, user_id, session_id, trip_name, destination, 
                          start_date, end_date, budget, travelers, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            trip_id,
            user_id,
            session_id,
            trip_data.get('trip_name', 'My Trip') if trip_data else 'My Trip',
            trip_data.get('destination', '') if trip_data else '',
            trip_data.get('start_date') if trip_data and trip_data.get('start_date') else None,
            trip_data.get('end_date') if trip_data and trip_data.get('end_date') else None,
            trip_data.get('budget', 0) if trip_data else 0,
            trip_data.get('travelers', 1) if trip_data else 1,
            'active'
        )
        
        result = execute_query(query, params, fetch=False)
        return result is not None
        
    except Exception as e:
        logger.error(f"Error creating trip: {e}")
        return False

def get_trip_db(trip_id, user_id=None, session_id=None):
    """Get a trip from the database with its destinations"""
    try:
        # Build query based on available identifiers
        if user_id:
            trip_query = """
            SELECT * FROM trips 
            WHERE id = %s AND (user_id = %s OR session_id = %s)
            """
            trip_params = (trip_id, user_id, session_id)
        else:
            trip_query = """
            SELECT * FROM trips 
            WHERE id = %s AND session_id = %s
            """
            trip_params = (trip_id, session_id)
        
        trip = execute_query(trip_query, trip_params)
        
        if not trip:
            return None
            
        trip = trip[0]
        
        # Get destinations for this trip
        destinations_query = """
        SELECT * FROM trip_destinations 
        WHERE trip_id = %s 
        ORDER BY order_index ASC, added_at ASC
        """
        destinations = execute_query(destinations_query, (trip_id,))
        
        # Get route data if available
        route_query = """
        SELECT * FROM trip_routes 
        WHERE trip_id = %s 
        ORDER BY calculated_at DESC 
        LIMIT 1
        """
        route_data = execute_query(route_query, (trip_id,))
        
        # Format the response
        trip_data = {
            'id': trip['id'],
            'trip_name': trip['trip_name'],
            'destination': trip['destination'],
            'start_date': trip['start_date'].isoformat() if trip['start_date'] else None,
            'end_date': trip['end_date'].isoformat() if trip['end_date'] else None,
            'budget': float(trip['budget']) if trip['budget'] else 0,
            'travelers': trip['travelers'],
            'status': trip['status'],
            'created_at': trip['created_at'].isoformat() if trip['created_at'] else None,
            'updated_at': trip['updated_at'].isoformat() if trip['updated_at'] else None,
            'destinations': []
        }
        
        # Add destinations
        for dest in destinations or []:
            destination_data = {
                'id': dest['id'],
                'destination_id': dest['destination_id'],
                'name': dest['name'],
                'city': dest['city'],
                'province': dest['province'],
                'description': dest['description'],
                'category': dest['category'],
                'rating': float(dest['rating']) if dest['rating'] else None,
                'budget': float(dest['budget']) if dest['budget'] else None,
                'latitude': float(dest['latitude']) if dest['latitude'] else None,
                'longitude': float(dest['longitude']) if dest['longitude'] else None,
                'operating_hours': dest['operating_hours'],
                'contact_information': dest['contact_information'],
                'order_index': dest['order_index']
            }
            trip_data['destinations'].append(destination_data)
        
        # Add route data if available
        if route_data:
            route = route_data[0]
            import json
            trip_data['route_data'] = {
                'points': json.loads(route['route_data']) if route['route_data'] else [],
                'distance_km': float(route['distance_km']) if route['distance_km'] else 0,
                'time_min': route['time_minutes'] if route['time_minutes'] else 0,
                'source': route['route_source']
            }
        
        return trip_data
        
    except Exception as e:
        logger.error(f"Error getting trip: {e}")
        return None

def update_trip_db(trip_id, trip_data, user_id=None, session_id=None):
    """Update a trip in the database"""
    try:
        # Build query based on available identifiers
        if user_id:
            query = """
            UPDATE trips 
            SET trip_name = %s, destination = %s, start_date = %s, 
                end_date = %s, budget = %s, travelers = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND (user_id = %s OR session_id = %s)
            """
            params = (
                trip_data.get('trip_name', 'My Trip'),
                trip_data.get('destination', ''),
                trip_data.get('start_date'),
                trip_data.get('end_date'),
                trip_data.get('budget', 0),
                trip_data.get('travelers', 1),
                trip_id,
                user_id,
                session_id
            )
        else:
            query = """
            UPDATE trips 
            SET trip_name = %s, destination = %s, start_date = %s, 
                end_date = %s, budget = %s, travelers = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND session_id = %s
            """
            params = (
                trip_data.get('trip_name', 'My Trip'),
                trip_data.get('destination', ''),
                trip_data.get('start_date'),
                trip_data.get('end_date'),
                trip_data.get('budget', 0),
                trip_data.get('travelers', 1),
                trip_id,
                session_id
            )
        
        result = execute_query(query, params, fetch=False)
        return result is not None
        
    except Exception as e:
        logger.error(f"Error updating trip: {e}")
        return False

def add_destination_to_trip_db(trip_id, destination_data):
    """Add a destination to a trip"""
    try:
        # Get the next order index
        order_query = """
        SELECT COALESCE(MAX(order_index), 0) + 1 as next_order 
        FROM trip_destinations 
        WHERE trip_id = %s
        """
        order_result = execute_query(order_query, (trip_id,))
        next_order = order_result[0]['next_order'] if order_result else 1
        
        query = """
        INSERT INTO trip_destinations (
            trip_id, destination_id, name, city, province, description, 
            category, rating, budget, latitude, longitude, 
            operating_hours, contact_information, order_index
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            trip_id,
            destination_data.get('id'),
            destination_data.get('name', ''),
            destination_data.get('city', ''),
            destination_data.get('province', ''),
            destination_data.get('description', ''),
            destination_data.get('category', ''),
            destination_data.get('rating'),
            destination_data.get('budget'),
            destination_data.get('latitude'),
            destination_data.get('longitude'),
            destination_data.get('operating_hours'),
            destination_data.get('contact_information'),
            next_order
        )
        
        destination_id = execute_query(query, params, fetch=False)
        return destination_id
        
    except Exception as e:
        logger.error(f"Error adding destination to trip: {e}")
        return None

def remove_destination_from_trip_db(trip_id, destination_id):
    """Remove a destination from a trip"""
    try:
        query = """
        DELETE FROM trip_destinations 
        WHERE trip_id = %s AND id = %s
        """
        
        result = execute_query(query, (trip_id, destination_id), fetch=False)
        return result is not None
        
    except Exception as e:
        logger.error(f"Error removing destination from trip: {e}")
        return False

def save_trip_route_db(trip_id, route_data):
    """Save route data for a trip"""
    try:
        import json
        
        # Delete existing route data for this trip
        delete_query = "DELETE FROM trip_routes WHERE trip_id = %s"
        execute_query(delete_query, (trip_id,), fetch=False)
        
        # Insert new route data
        query = """
        INSERT INTO trip_routes (trip_id, route_data, distance_km, time_minutes, route_source)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        params = (
            trip_id,
            json.dumps(route_data.get('points', [])),
            route_data.get('distance_km'),
            route_data.get('time_min'),
            route_data.get('source', 'unknown')
        )
        
        result = execute_query(query, params, fetch=False)
        return result is not None
        
    except Exception as e:
        logger.error(f"Error saving trip route: {e}")
        return False

def get_user_trips_db(user_id):
    """Get all trips for a user"""
    try:
        query = """
        SELECT t.*, 
               COUNT(td.id) as destination_count,
               CASE WHEN tr.id IS NOT NULL THEN 1 ELSE 0 END as has_route
        FROM trips t
        LEFT JOIN trip_destinations td ON t.id = td.trip_id
        LEFT JOIN trip_routes tr ON t.id = tr.trip_id
        WHERE t.user_id = %s
        GROUP BY t.id
        ORDER BY t.updated_at DESC
        """
        
        trips = execute_query(query, (user_id,))
        
        # Format the response
        formatted_trips = []
        for trip in trips or []:
            trip_data = {
                'id': trip['id'],
                'trip_name': trip['trip_name'],
                'destination': trip['destination'],
                'start_date': trip['start_date'].isoformat() if trip['start_date'] else None,
                'end_date': trip['end_date'].isoformat() if trip['end_date'] else None,
                'budget': float(trip['budget']) if trip['budget'] else 0,
                'travelers': trip['travelers'],
                'status': trip['status'],
                'created_at': trip['created_at'].isoformat() if trip['created_at'] else None,
                'updated_at': trip['updated_at'].isoformat() if trip['updated_at'] else None,
                'destination_count': trip['destination_count'],
                'has_route': bool(trip['has_route'])
            }
            formatted_trips.append(trip_data)
        
        return formatted_trips
        
    except Exception as e:
        logger.error(f"Error getting user trips: {e}")
        return []

# Generated Ticket ID Functions

def save_generated_ticket_db(ticket_id, ticket_type, user_id=None, session_id=None, include_timestamp=True, metadata=None):
    """Save a generated ticket ID to the database"""
    try:
        import json
        
        query = """
        INSERT INTO generated_tickets (
            ticket_id, ticket_type, user_id, session_id, 
            include_timestamp, metadata
        ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        params = (
            ticket_id,
            ticket_type,
            user_id,
            session_id,
            include_timestamp,
            json.dumps(metadata) if metadata else None
        )
        
        result = execute_query(query, params, fetch=False)
        return result is not None
        
    except Exception as e:
        logger.error(f"Error saving generated ticket: {e}")
        return False

def get_generated_tickets_db(user_id=None, session_id=None, limit=50):
    """Get generated tickets for a user or session"""
    try:
        if user_id:
            query = """
            SELECT * FROM generated_tickets 
            WHERE user_id = %s OR session_id = %s
            ORDER BY created_at DESC 
            LIMIT %s
            """
            params = (user_id, session_id, limit)
        else:
            query = """
            SELECT * FROM generated_tickets 
            WHERE session_id = %s
            ORDER BY created_at DESC 
            LIMIT %s
            """
            params = (session_id, limit)
        
        tickets = execute_query(query, params)
        
        # Format the response
        formatted_tickets = []
        for ticket in tickets or []:
            import json
            ticket_data = {
                'id': ticket['id'],
                'ticket_id': ticket['ticket_id'],
                'ticket_type': ticket['ticket_type'],
                'is_used': bool(ticket['is_used']),
                'used_at': ticket['used_at'].isoformat() if ticket['used_at'] else None,
                'include_timestamp': bool(ticket['include_timestamp']),
                'metadata': json.loads(ticket['metadata']) if ticket['metadata'] else {},
                'created_at': ticket['created_at'].isoformat() if ticket['created_at'] else None,
                'updated_at': ticket['updated_at'].isoformat() if ticket['updated_at'] else None
            }
            formatted_tickets.append(ticket_data)
        
        return formatted_tickets
        
    except Exception as e:
        logger.error(f"Error getting generated tickets: {e}")
        return []

def mark_ticket_as_used_db(ticket_id, user_id=None, session_id=None):
    """Mark a generated ticket as used"""
    try:
        if user_id:
            query = """
            UPDATE generated_tickets 
            SET is_used = TRUE, used_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE ticket_id = %s AND (user_id = %s OR session_id = %s)
            """
            params = (ticket_id, user_id, session_id)
        else:
            query = """
            UPDATE generated_tickets 
            SET is_used = TRUE, used_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE ticket_id = %s AND session_id = %s
            """
            params = (ticket_id, session_id)
        
        result = execute_query(query, params, fetch=False)
        return result is not None
        
    except Exception as e:
        logger.error(f"Error marking ticket as used: {e}")
        return False

def get_ticket_stats_db(user_id=None, session_id=None):
    """Get statistics for generated tickets"""
    try:
        if user_id:
            query = """
            SELECT 
                COUNT(*) as total_generated,
                SUM(CASE WHEN is_used = TRUE THEN 1 ELSE 0 END) as total_used,
                SUM(CASE WHEN is_used = FALSE THEN 1 ELSE 0 END) as total_unused,
                ticket_type,
                COUNT(*) as type_count
            FROM generated_tickets 
            WHERE user_id = %s OR session_id = %s
            GROUP BY ticket_type
            """
            params = (user_id, session_id)
        else:
            query = """
            SELECT 
                COUNT(*) as total_generated,
                SUM(CASE WHEN is_used = TRUE THEN 1 ELSE 0 END) as total_used,
                SUM(CASE WHEN is_used = FALSE THEN 1 ELSE 0 END) as total_unused,
                ticket_type,
                COUNT(*) as type_count
            FROM generated_tickets 
            WHERE session_id = %s
            GROUP BY ticket_type
            """
            params = (session_id,)
        
        # Get overall stats
        if user_id:
            total_query = """
            SELECT 
                COUNT(*) as total_generated,
                SUM(CASE WHEN is_used = TRUE THEN 1 ELSE 0 END) as total_used,
                SUM(CASE WHEN is_used = FALSE THEN 1 ELSE 0 END) as total_unused
            FROM generated_tickets 
            WHERE user_id = %s OR session_id = %s
            """
            total_params = (user_id, session_id)
        else:
            total_query = """
            SELECT 
                COUNT(*) as total_generated,
                SUM(CASE WHEN is_used = TRUE THEN 1 ELSE 0 END) as total_used,
                SUM(CASE WHEN is_used = FALSE THEN 1 ELSE 0 END) as total_unused
            FROM generated_tickets 
            WHERE session_id = %s
            """
            total_params = (session_id,)
        
        total_stats = execute_query(total_query, total_params)
        type_stats = execute_query(query, params)
        
        # Format response
        stats = {
            'total_generated': total_stats[0]['total_generated'] if total_stats else 0,
            'total_used': total_stats[0]['total_used'] if total_stats else 0,
            'total_unused': total_stats[0]['total_unused'] if total_stats else 0,
            'type_stats': {}
        }
        
        for stat in type_stats or []:
            stats['type_stats'][stat['ticket_type']] = stat['type_count']
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting ticket stats: {e}")
        return {
            'total_generated': 0,
            'total_used': 0,
            'total_unused': 0,
            'type_stats': {}
        }

def clear_generated_tickets_db(user_id=None, session_id=None):
    """Clear all generated tickets for a user or session"""
    try:
        if user_id:
            query = """
            DELETE FROM generated_tickets 
            WHERE user_id = %s OR session_id = %s
            """
            params = (user_id, session_id)
        else:
            query = """
            DELETE FROM generated_tickets 
            WHERE session_id = %s
            """
            params = (session_id,)
        
        result = execute_query(query, params, fetch=False)
        return result is not None
        
    except Exception as e:
        logger.error(f"Error clearing generated tickets: {e}")
        return False

def check_ticket_exists_db(ticket_id):
    """Check if a ticket ID already exists in the database"""
    try:
        query = "SELECT COUNT(*) as count FROM generated_tickets WHERE ticket_id = %s"
        result = execute_query(query, (ticket_id,))
        return result[0]['count'] > 0 if result else False
        
    except Exception as e:
        logger.error(f"Error checking ticket existence: {e}")
        return False

# Trip Tracker Functions

def save_trip_tracker_db(tracker_id, trip_id, email, traveler_name=None, phone=None, expires_at=None):
    """Save a trip tracker to the database"""
    try:
        query = """
        INSERT INTO trip_trackers (
            tracker_id, trip_id, email, traveler_name, phone, expires_at
        ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        params = (
            tracker_id,
            trip_id,
            email,
            traveler_name,
            phone,
            expires_at
        )
        
        result = execute_query(query, params, fetch=False)
        return result is not None
        
    except Exception as e:
        logger.error(f"Error saving trip tracker: {e}")
        return False

def get_trip_db_for_tracker(trip_id):
    """Get a trip from the database for tracker access (bypasses user/session check)"""
    try:
        # Get trip data without user/session restrictions
        trip_query = "SELECT * FROM trips WHERE id = %s"
        trip = execute_query(trip_query, (trip_id,))
        
        if not trip:
            return None
            
        trip = trip[0]
        
        # Get destinations for this trip
        destinations_query = """
        SELECT * FROM trip_destinations 
        WHERE trip_id = %s 
        ORDER BY order_index ASC, added_at ASC
        """
        destinations = execute_query(destinations_query, (trip_id,))
        
        # Get route data if available
        route_query = """
        SELECT * FROM trip_routes 
        WHERE trip_id = %s 
        ORDER BY calculated_at DESC 
        LIMIT 1
        """
        route_data = execute_query(route_query, (trip_id,))
        
        # Format the response
        trip_data = {
            'id': trip['id'],
            'trip_name': trip['trip_name'],
            'destination': trip['destination'],
            'start_date': trip['start_date'].isoformat() if trip['start_date'] else None,
            'end_date': trip['end_date'].isoformat() if trip['end_date'] else None,
            'budget': float(trip['budget']) if trip['budget'] else 0,
            'travelers': trip['travelers'],
            'status': trip['status'],
            'created_at': trip['created_at'].isoformat() if trip['created_at'] else None,
            'updated_at': trip['updated_at'].isoformat() if trip['updated_at'] else None,
            'destinations': []
        }
        
        # Add destinations
        for dest in destinations or []:
            destination_data = {
                'id': dest['id'],
                'destination_id': dest['destination_id'],
                'name': dest['name'],
                'city': dest['city'],
                'province': dest['province'],
                'description': dest['description'],
                'category': dest['category'],
                'rating': float(dest['rating']) if dest['rating'] else None,
                'budget': float(dest['budget']) if dest['budget'] else None,
                'latitude': float(dest['latitude']) if dest['latitude'] else None,
                'longitude': float(dest['longitude']) if dest['longitude'] else None,
                'operating_hours': dest['operating_hours'],
                'contact_information': dest['contact_information'],
                'order_index': dest['order_index']
            }
            trip_data['destinations'].append(destination_data)
        
        # Add route data if available
        if route_data:
            route = route_data[0]
            import json
            trip_data['route_data'] = {
                'points': json.loads(route['route_data']) if route['route_data'] else [],
                'distance_km': float(route['distance_km']) if route['distance_km'] else 0,
                'time_min': route['time_minutes'] if route['time_minutes'] else 0,
                'source': route['route_source']
            }
        
        return trip_data
        
    except Exception as e:
        logger.error(f"Error getting trip for tracker: {e}")
        return None

def get_trip_by_tracker_db(tracker_id, email=None):
    """Get a trip by tracker ID and optionally verify email"""
    try:
        if email:
            query = """
            SELECT tt.*, t.* 
            FROM trip_trackers tt
            JOIN trips t ON tt.trip_id = t.id
            WHERE tt.tracker_id = %s AND tt.email = %s AND tt.is_active = TRUE
            """
            params = (tracker_id, email)
        else:
            query = """
            SELECT tt.*, t.* 
            FROM trip_trackers tt
            JOIN trips t ON tt.trip_id = t.id
            WHERE tt.tracker_id = %s AND tt.is_active = TRUE
            """
            params = (tracker_id,)
        
        result = execute_query(query, params)
        
        if result:
            tracker_data = result[0]
            
            # Update access count and last accessed
            update_query = """
            UPDATE trip_trackers 
            SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP
            WHERE tracker_id = %s
            """
            execute_query(update_query, (tracker_id,), fetch=False)
            
            # Get full trip data including destinations
            # For trip trackers, we need to bypass the user/session check
            trip_data = get_trip_db_for_tracker(tracker_data['trip_id'])
            
            if trip_data:
                # Add tracker information
                trip_data['tracker_info'] = {
                    'tracker_id': tracker_data['tracker_id'],
                    'email': tracker_data['email'],
                    'traveler_name': tracker_data['traveler_name'],
                    'phone': tracker_data['phone'],
                    'access_count': tracker_data['access_count'] + 1,
                    'created_at': tracker_data['created_at'].isoformat() if tracker_data['created_at'] else None
                }
                
            return trip_data
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting trip by tracker: {e}")
        return None

def get_trip_trackers_by_email_db(email):
    """Get all trip trackers for an email address"""
    try:
        query = """
        SELECT tt.*, t.trip_name, t.destination, t.start_date, t.end_date
        FROM trip_trackers tt
        JOIN trips t ON tt.trip_id = t.id
        WHERE tt.email = %s AND tt.is_active = TRUE
        ORDER BY tt.created_at DESC
        """
        
        trackers = execute_query(query, (email,))
        
        formatted_trackers = []
        for tracker in trackers or []:
            tracker_data = {
                'tracker_id': tracker['tracker_id'],
                'trip_name': tracker['trip_name'],
                'destination': tracker['destination'],
                'start_date': tracker['start_date'].isoformat() if tracker['start_date'] else None,
                'end_date': tracker['end_date'].isoformat() if tracker['end_date'] else None,
                'traveler_name': tracker['traveler_name'],
                'access_count': tracker['access_count'],
                'created_at': tracker['created_at'].isoformat() if tracker['created_at'] else None
            }
            formatted_trackers.append(tracker_data)
        
        return formatted_trackers
        
    except Exception as e:
        logger.error(f"Error getting trip trackers by email: {e}")
        return []

def check_tracker_exists_db(tracker_id):
    """Check if a tracker ID already exists in the database"""
    try:
        query = "SELECT COUNT(*) as count FROM trip_trackers WHERE tracker_id = %s"
        result = execute_query(query, (tracker_id,))
        return result[0]['count'] > 0 if result else False
        
    except Exception as e:
        logger.error(f"Error checking tracker existence: {e}")
        return False

def deactivate_trip_tracker_db(tracker_id, email):
    """Deactivate a trip tracker"""
    try:
        query = """
        UPDATE trip_trackers 
        SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
        WHERE tracker_id = %s AND email = %s
        """
        
        result = execute_query(query, (tracker_id, email), fetch=False)
        return result is not None
        
    except Exception as e:
        logger.error(f"Error deactivating trip tracker: {e}")
        return False

if __name__ == "__main__":
    # Test database connection
    conn = get_connection()
    if conn:
        print("Database connection successful!")
        conn.close()
    else:
        print("Failed to connect to database!") 