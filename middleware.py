from functools import wraps
from flask import request, jsonify, session
import logging
from auth import validate_session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def login_required(f):
    """Middleware to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        session_id = request.headers.get('X-Session-ID') or session.get('session_id')
        user_session = validate_session(session_id)
        
        if not user_session:
            return jsonify({
                "success": False,
                "message": "Authentication required"
            }), 401
        
        # Add user data to kwargs
        kwargs['user_id'] = user_session['user_id']
        kwargs['username'] = user_session['username']
        kwargs['email'] = user_session['email']
        
        return f(*args, **kwargs)
    
    return decorated_function

def admin_required(f):
    """Middleware to require admin privileges for admin routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        session_id = request.headers.get('X-Session-ID') or session.get('session_id')
        user_session = validate_session(session_id)
        
        if not user_session:
            return jsonify({
                "success": False,
                "message": "Authentication required"
            }), 401
        
        # TODO: Implement admin check here
        # For now, this is a placeholder
        # You would typically query the database to check if the user has admin role
        
        # Add user data to kwargs
        kwargs['user_id'] = user_session['user_id']
        kwargs['username'] = user_session['username']
        kwargs['email'] = user_session['email']
        
        return f(*args, **kwargs)
    
    return decorated_function

def log_request(f):
    """Middleware to log API requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Log request information
        logger.info(f"Request: {request.method} {request.path}")
        
        # Call the original function
        response = f(*args, **kwargs)
        
        # Log response status
        if isinstance(response, tuple):
            status_code = response[1]
        else:
            status_code = 200
        
        logger.info(f"Response: {status_code}")
        
        return response
    
    return decorated_function 