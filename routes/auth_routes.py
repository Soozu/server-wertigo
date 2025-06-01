from flask import Blueprint, request, jsonify, session
import logging
from datetime import datetime
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import (
    register_user, login_user, logout_user, 
    validate_session, get_user_profile, update_user_profile
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Blueprint for auth routes
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "Invalid request data"
            }), 400
            
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        
        result = register_user(username, email, password, first_name, last_name)
        
        if result["success"]:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error in register route: {e}")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login a user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "Invalid request data"
            }), 400
            
        username = data.get('username')  # Can be username or email
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                "success": False,
                "message": "Username and password are required"
            }), 400
            
        result = login_user(username, password)
        
        if result["success"]:
            # Store session ID in Flask session
            session['session_id'] = result["session_id"]
            session['user_id'] = result["user"]["id"]
            session['login_time'] = datetime.now().isoformat()
            
            return jsonify(result), 200
        else:
            return jsonify(result), 401
            
    except Exception as e:
        logger.error(f"Error in login route: {e}")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout a user"""
    try:
        # Get session ID either from request or from Flask session
        data = request.get_json() or {}
        session_id = data.get('session_id') or session.get('session_id')
        
        result = logout_user(session_id)
        
        if result["success"]:
            # Clear Flask session
            session.clear()
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error in logout route: {e}")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500

@auth_bp.route('/profile', methods=['GET'])
def profile():
    """Get user profile"""
    try:
        # Check if user is logged in
        session_id = request.headers.get('X-Session-ID') or session.get('session_id')
        user_session = validate_session(session_id)
        
        if not user_session:
            return jsonify({
                "success": False,
                "message": "Not authenticated"
            }), 401
            
        user_profile = get_user_profile(user_session["user_id"])
        
        if user_profile:
            return jsonify({
                "success": True,
                "profile": user_profile
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404
            
    except Exception as e:
        logger.error(f"Error in profile route: {e}")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500

@auth_bp.route('/profile', methods=['PUT'])
def update_profile():
    """Update user profile"""
    try:
        # Check if user is logged in
        session_id = request.headers.get('X-Session-ID') or session.get('session_id')
        user_session = validate_session(session_id)
        
        if not user_session:
            return jsonify({
                "success": False,
                "message": "Not authenticated"
            }), 401
            
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "Invalid request data"
            }), 400
            
        result = update_user_profile(
            user_session["user_id"],
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            password=data.get('password')
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error in update_profile route: {e}")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500

@auth_bp.route('/validate', methods=['GET'])
def validate():
    """Validate a session"""
    try:
        session_id = request.headers.get('X-Session-ID') or session.get('session_id')
        user_session = validate_session(session_id)
        
        if user_session:
            return jsonify({
                "success": True,
                "message": "Session is valid",
                "user": {
                    "id": user_session["user_id"],
                    "username": user_session["username"],
                    "email": user_session["email"]
                }
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Session is invalid or expired"
            }), 401
            
    except Exception as e:
        logger.error(f"Error in validate route: {e}")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500 