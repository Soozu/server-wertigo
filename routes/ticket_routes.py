from flask import Blueprint, request, jsonify, session
from middleware import login_required
from db import (
    save_generated_ticket_db, 
    get_generated_tickets_db, 
    mark_ticket_as_used_db,
    get_ticket_stats_db,
    clear_generated_tickets_db,
    check_ticket_exists_db,
    save_trip_tracker_db,
    get_trip_by_tracker_db,
    get_trip_trackers_by_email_db,
    check_tracker_exists_db,
    deactivate_trip_tracker_db
)
import logging
import uuid
import random
import string
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
ticket_bp = Blueprint('tickets', __name__)

# Ticket ID formats for different services
TICKET_FORMATS = {
    'FLIGHT': 'FL',
    'BUS': 'BS', 
    'FERRY': 'FR',
    'TRAIN': 'TR',
    'HOTEL': 'HT',
    'TOUR': 'TO'
}

def generate_random_string(length):
    """Generate random alphanumeric string"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def generate_timestamp():
    """Generate timestamp-based ID component"""
    now = datetime.now()
    year = str(now.year)[-2:]
    month = str(now.month).zfill(2)
    day = str(now.day).zfill(2)
    return f"{year}{month}{day}"

def generate_ticket_id(ticket_type='FLIGHT', include_timestamp=True):
    """Generate ticket ID with specific format"""
    prefix = TICKET_FORMATS.get(ticket_type, 'TK')
    timestamp = generate_timestamp() if include_timestamp else ''
    random_part = generate_random_string(6)
    
    return f"{prefix}{timestamp}{random_part}"

def generate_booking_reference():
    """Generate booking reference (shorter format)"""
    return generate_random_string(6)

def generate_confirmation_number():
    """Generate confirmation number"""
    letters = generate_random_string(2)
    numbers = str(random.randint(1000, 9999))
    return f"{letters}{numbers}"

def generate_trip_tracker_id():
    """Generate trip tracker ID with format TR + 8 characters"""
    return f"TR{generate_random_string(8)}"

def generate_unique_ticket_id(ticket_type, include_timestamp=True, max_attempts=100):
    """Generate unique ticket ID that doesn't exist in database"""
    for attempt in range(max_attempts):
        if ticket_type == 'BOOKING_REF':
            ticket_id = generate_booking_reference()
        elif ticket_type == 'CONFIRMATION':
            ticket_id = generate_confirmation_number()
        else:
            ticket_id = generate_ticket_id(ticket_type, include_timestamp)
        
        # Check if ID already exists in database
        if not check_ticket_exists_db(ticket_id):
            return ticket_id
    
    # Fallback: add random suffix
    base_id = generate_ticket_id(ticket_type, include_timestamp)
    return f"{base_id}{random.randint(10, 99)}"

def generate_unique_trip_tracker_id(max_attempts=100):
    """Generate unique trip tracker ID that doesn't exist in database"""
    for attempt in range(max_attempts):
        tracker_id = generate_trip_tracker_id()
        
        # Check if ID already exists in database
        if not check_tracker_exists_db(tracker_id):
            return tracker_id
    
    # Fallback: add random suffix
    base_id = generate_trip_tracker_id()
    return f"{base_id}{random.randint(10, 99)}"

@ticket_bp.route('/generate', methods=['POST'])
def generate_ticket():
    """Generate a new ticket ID"""
    try:
        data = request.get_json()
        ticket_type = data.get('type', 'FLIGHT')
        include_timestamp = data.get('include_timestamp', True)
        metadata = data.get('metadata', {})
        
        # Get user info
        user_id = session.get('user_id')
        session_id = session.get('session_id', str(uuid.uuid4()))
        
        # Generate unique ticket ID
        ticket_id = generate_unique_ticket_id(ticket_type, include_timestamp)
        
        # Save to database
        success = save_generated_ticket_db(
            ticket_id=ticket_id,
            ticket_type=ticket_type,
            user_id=user_id,
            session_id=session_id,
            include_timestamp=include_timestamp,
            metadata=metadata
        )
        
        if success:
            return jsonify({
                'success': True,
                'ticket_id': ticket_id,
                'type': ticket_type,
                'include_timestamp': include_timestamp,
                'created_at': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save ticket to database'
            }), 500
            
    except Exception as e:
        logger.error(f"Error generating ticket: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ticket_bp.route('/history', methods=['GET'])
def get_ticket_history():
    """Get ticket generation history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        # Get user info
        user_id = session.get('user_id')
        session_id = session.get('session_id')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session found'
            }), 400
        
        # Get tickets from database
        tickets = get_generated_tickets_db(user_id, session_id, limit)
        
        return jsonify({
            'success': True,
            'tickets': tickets,
            'count': len(tickets)
        })
        
    except Exception as e:
        logger.error(f"Error getting ticket history: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ticket_bp.route('/mark-used', methods=['POST'])
def mark_ticket_used():
    """Mark a ticket as used"""
    try:
        data = request.get_json()
        ticket_id = data.get('ticket_id')
        
        if not ticket_id:
            return jsonify({
                'success': False,
                'error': 'Ticket ID is required'
            }), 400
        
        # Get user info
        user_id = session.get('user_id')
        session_id = session.get('session_id')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session found'
            }), 400
        
        # Mark ticket as used
        success = mark_ticket_as_used_db(ticket_id, user_id, session_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Ticket marked as used',
                'ticket_id': ticket_id,
                'used_at': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to mark ticket as used'
            }), 500
            
    except Exception as e:
        logger.error(f"Error marking ticket as used: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ticket_bp.route('/stats', methods=['GET'])
def get_ticket_stats():
    """Get ticket generation statistics"""
    try:
        # Get user info
        user_id = session.get('user_id')
        session_id = session.get('session_id')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session found'
            }), 400
        
        # Get stats from database
        stats = get_ticket_stats_db(user_id, session_id)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting ticket stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ticket_bp.route('/clear', methods=['DELETE'])
def clear_tickets():
    """Clear all generated tickets"""
    try:
        # Get user info
        user_id = session.get('user_id')
        session_id = session.get('session_id')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'No session found'
            }), 400
        
        # Clear tickets from database
        success = clear_generated_tickets_db(user_id, session_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'All tickets cleared successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to clear tickets'
            }), 500
            
    except Exception as e:
        logger.error(f"Error clearing tickets: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ticket_bp.route('/validate', methods=['POST'])
def validate_ticket():
    """Validate a ticket ID format"""
    try:
        data = request.get_json()
        ticket_id = data.get('ticket_id')
        
        if not ticket_id:
            return jsonify({
                'success': False,
                'error': 'Ticket ID is required'
            }), 400
        
        # Validate format
        valid_prefixes = list(TICKET_FORMATS.values())
        has_valid_prefix = any(ticket_id.startswith(prefix) for prefix in valid_prefixes)
        has_valid_length = len(ticket_id) >= 8
        
        is_valid = has_valid_prefix and has_valid_length
        
        # Get ticket type
        ticket_type = 'UNKNOWN'
        for type_name, prefix in TICKET_FORMATS.items():
            if ticket_id.startswith(prefix):
                ticket_type = type_name
                break
        
        # Check if exists in database
        exists_in_db = check_ticket_exists_db(ticket_id)
        
        return jsonify({
            'success': True,
            'valid': is_valid,
            'ticket_type': ticket_type,
            'exists_in_database': exists_in_db,
            'ticket_id': ticket_id
        })
        
    except Exception as e:
        logger.error(f"Error validating ticket: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ticket_bp.route('/search', methods=['POST'])
def search_ticket():
    """Search for a ticket or trip tracker by ID (for TicketTracker functionality)"""
    try:
        data = request.get_json()
        ticket_id = data.get('ticketId')
        email = data.get('email')
        
        if not ticket_id and not email:
            return jsonify({
                'success': False,
                'error': 'Ticket ID or email is required'
            }), 400
        
        if ticket_id:
            # Check if it's a trip tracker ID (starts with TR)
            if ticket_id.startswith('TR'):
                trip_data = get_trip_by_tracker_db(ticket_id, email)
                
                if trip_data:
                    return jsonify({
                        'success': True,
                        'type': 'trip',
                        'trip': trip_data
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Trip tracker not found or access denied'
                    }), 404
            
            # Check if ticket exists in our generated tickets
            exists = check_ticket_exists_db(ticket_id)
            
            if exists:
                # Return mock ticket details
                return jsonify({
                    'success': True,
                    'type': 'ticket',
                    'ticket': {
                        'id': ticket_id,
                        'type': 'FLIGHT',
                        'status': 'CONFIRMED',
                        'passenger_name': 'John Doe',
                        'departure': 'Manila (MNL)',
                        'arrival': 'Cebu (CEB)',
                        'departure_time': '2024-12-20T10:30:00',
                        'arrival_time': '2024-12-20T12:15:00',
                        'seat': '12A',
                        'gate': 'A5',
                        'booking_reference': generate_booking_reference(),
                        'created_at': datetime.now().isoformat()
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Ticket not found'
                }), 404
        
        # Email search - return both tickets and trip trackers
        if email:
            # Get trip trackers
            trip_trackers = get_trip_trackers_by_email_db(email)
            
            # Mock tickets for email search
            mock_tickets = [
                {
                    'id': generate_ticket_id('FLIGHT'),
                    'type': 'FLIGHT',
                    'status': 'CONFIRMED',
                    'departure': 'Manila (MNL)',
                    'arrival': 'Cebu (CEB)',
                    'departure_time': '2024-12-20T10:30:00'
                }
            ]
            
            return jsonify({
                'success': True,
                'type': 'email_search',
                'tickets': mock_tickets,
                'trip_trackers': trip_trackers
            })
        
    except Exception as e:
        logger.error(f"Error searching ticket: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

# Trip Tracker Routes

@ticket_bp.route('/save-trip', methods=['POST'])
def save_trip_tracker():
    """Save a trip with tracker ID for sharing"""
    try:
        data = request.get_json()
        trip_id = data.get('trip_id')
        email = data.get('email')
        traveler_name = data.get('traveler_name', '')
        phone = data.get('phone', '')
        
        if not trip_id or not email:
            return jsonify({
                'success': False,
                'error': 'Trip ID and email are required'
            }), 400
        
        # Generate unique tracker ID
        tracker_id = generate_unique_trip_tracker_id()
        
        # Save trip tracker
        success = save_trip_tracker_db(
            tracker_id=tracker_id,
            trip_id=trip_id,
            email=email,
            traveler_name=traveler_name,
            phone=phone
        )
        
        if success:
            return jsonify({
                'success': True,
                'tracker_id': tracker_id,
                'message': 'Trip saved successfully! You can now track it using the tracker ID.',
                'email': email,
                'created_at': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save trip tracker'
            }), 500
            
    except Exception as e:
        logger.error(f"Error saving trip tracker: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ticket_bp.route('/track-trip', methods=['POST'])
def track_trip():
    """Track a trip using tracker ID and email"""
    try:
        data = request.get_json()
        tracker_id = data.get('tracker_id')
        email = data.get('email')
        
        if not tracker_id:
            return jsonify({
                'success': False,
                'error': 'Tracker ID is required'
            }), 400
        
        # Get trip by tracker ID
        trip_data = get_trip_by_tracker_db(tracker_id, email)
        
        if trip_data:
            return jsonify({
                'success': True,
                'trip': trip_data,
                'tracker_id': tracker_id
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Trip not found or access denied'
            }), 404
            
    except Exception as e:
        logger.error(f"Error tracking trip: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ticket_bp.route('/my-trackers', methods=['POST'])
def get_my_trackers():
    """Get all trip trackers for an email address"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'Email is required'
            }), 400
        
        # Get trackers by email
        trackers = get_trip_trackers_by_email_db(email)
        
        return jsonify({
            'success': True,
            'trackers': trackers,
            'count': len(trackers)
        })
        
    except Exception as e:
        logger.error(f"Error getting trip trackers: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@ticket_bp.route('/formats', methods=['GET'])
def get_ticket_formats():
    """Get available ticket formats"""
    return jsonify({
        'success': True,
        'formats': TICKET_FORMATS
    }) 