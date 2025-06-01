import uuid
import hashlib
import os
import logging
from datetime import datetime, timedelta
import re
import base64
from db import execute_query, get_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password validation regex - at least 6 characters
PASSWORD_PATTERN = r"^.{6,}$"
EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

def hash_password(password, salt=None):
    """Hash a password with salt using SHA-256"""
    if not salt:
        salt = os.urandom(32)  # Generate a new salt if not provided
    
    # Hash the password with the salt
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000  # Number of iterations
    )
    
    # Combine salt and key, then encode as base64 for database storage
    combined = salt + key
    return base64.b64encode(combined).decode('utf-8')

def verify_password(stored_password, provided_password):
    """Verify a password against its hash"""
    try:
        # Decode the base64 stored password
        combined = base64.b64decode(stored_password.encode('utf-8'))
        
        # Extract the salt from the stored password hash (first 32 bytes)
        salt = combined[:32]
        
        # Hash the provided password with the extracted salt
        new_hash = hash_password(provided_password, salt)
        
        # Compare the new hash with the stored hash
        return new_hash == stored_password
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False

def validate_registration_data(username, email, password):
    """Validate user registration data"""
    errors = {}
    
    # Validate username
    if not username or len(username) < 3:
        errors["username"] = "Username must be at least 3 characters long"
    
    # Validate email
    if not email or not re.match(EMAIL_PATTERN, email):
        errors["email"] = "Please provide a valid email address"
    
    # Validate password
    if not password or not re.match(PASSWORD_PATTERN, password):
        errors["password"] = "Password must be at least 6 characters long"
    
    return errors

def register_user(username, email, password, first_name=None, last_name=None):
    """Register a new user"""
    # Validate input data
    validation_errors = validate_registration_data(username, email, password)
    if validation_errors:
        return {
            "success": False,
            "message": "Validation failed",
            "errors": validation_errors
        }
    
    # Check if username or email already exists
    existing_user = execute_query(
        "SELECT id FROM users WHERE username = %s OR email = %s",
        (username, email)
    )
    
    if existing_user:
        return {
            "success": False,
            "message": "Username or email already exists",
            "errors": {
                "username": "Username or email already exists"
            }
        }
    
    # Hash the password
    hashed_password = hash_password(password)
    
    # Insert the new user
    try:
        user_id = execute_query(
            """
            INSERT INTO users (username, email, password, first_name, last_name)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (username, email, hashed_password, first_name, last_name),
            fetch=False
        )
        
        if user_id:
            return {
                "success": True,
                "message": "User registered successfully",
                "user_id": user_id
            }
        else:
            return {
                "success": False,
                "message": "Failed to register user",
                "errors": {"general": "Database error"}
            }
            
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        return {
            "success": False,
            "message": "Failed to register user",
            "errors": {"general": str(e)}
        }

def login_user(username, password):
    """Authenticate a user and create a session"""
    # Get user by username or email
    user = execute_query(
        "SELECT id, username, email, password FROM users WHERE username = %s OR email = %s",
        (username, username)
    )
    
    if not user:
        return {
            "success": False,
            "message": "Invalid username or password"
        }
    
    user = user[0]  # Get the first user (should be only one)
    
    # Verify password
    if not verify_password(user["password"], password):
        return {
            "success": False,
            "message": "Invalid username or password"
        }
    
    # Create a session
    session_id = str(uuid.uuid4())
    expiry = datetime.now() + timedelta(days=1)  # 24-hour session
    
    # Store session in database
    session_created = execute_query(
        """
        INSERT INTO user_sessions (user_id, session_id, expires_at)
        VALUES (%s, %s, %s)
        """,
        (user["id"], session_id, expiry),
        fetch=False
    )
    
    if session_created:
        return {
            "success": True,
            "message": "Login successful",
            "session_id": session_id,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"]
            }
        }
    else:
        return {
            "success": False,
            "message": "Failed to create session"
        }

def validate_session(session_id):
    """Validate a user session"""
    if not session_id:
        return None
    
    # Get session data
    session = execute_query(
        """
        SELECT us.*, u.username, u.email 
        FROM user_sessions us
        JOIN users u ON us.user_id = u.id
        WHERE us.session_id = %s AND us.expires_at > NOW()
        """,
        (session_id,)
    )
    
    if not session:
        return None
    
    session = session[0]
    
    return {
        "user_id": session["user_id"],
        "username": session["username"],
        "email": session["email"],
        "session_id": session["session_id"],
        "expires_at": session["expires_at"]
    }

def logout_user(session_id):
    """End a user session"""
    if not session_id:
        return {
            "success": False,
            "message": "No session ID provided"
        }
    
    # Delete the session
    result = execute_query(
        "DELETE FROM user_sessions WHERE session_id = %s",
        (session_id,),
        fetch=False
    )
    
    if result is not None:
        return {
            "success": True,
            "message": "Logged out successfully"
        }
    else:
        return {
            "success": False,
            "message": "Failed to logout"
        }

def get_user_profile(user_id):
    """Get user profile data"""
    user = execute_query(
        """
        SELECT id, username, email, first_name, last_name, created_at 
        FROM users WHERE id = %s
        """,
        (user_id,)
    )
    
    if not user:
        return None
    
    return user[0]

def update_user_profile(user_id, first_name=None, last_name=None, email=None, password=None):
    """Update user profile data"""
    updates = []
    params = []
    
    if first_name is not None:
        updates.append("first_name = %s")
        params.append(first_name)
    
    if last_name is not None:
        updates.append("last_name = %s")
        params.append(last_name)
    
    if email is not None:
        # Validate email
        if not re.match(EMAIL_PATTERN, email):
            return {
                "success": False,
                "message": "Invalid email address"
            }
        
        # Check if email already exists for another user
        existing = execute_query(
            "SELECT id FROM users WHERE email = %s AND id != %s",
            (email, user_id)
        )
        
        if existing:
            return {
                "success": False,
                "message": "Email address already in use"
            }
        
        updates.append("email = %s")
        params.append(email)
    
    if password is not None:
        # Validate password
        if not re.match(PASSWORD_PATTERN, password):
            return {
                "success": False,
                "message": "Password must be at least 6 characters long"
            }
        
        # Hash new password
        hashed_password = hash_password(password)
        updates.append("password = %s")
        params.append(hashed_password)
    
    if not updates:
        return {
            "success": False,
            "message": "No updates provided"
        }
    
    # Build the query
    query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
    params.append(user_id)
    
    # Execute the update
    result = execute_query(query, params, fetch=False)
    
    if result is not None:
        return {
            "success": True,
            "message": "Profile updated successfully"
        }
    else:
        return {
            "success": False,
            "message": "Failed to update profile"
        } 