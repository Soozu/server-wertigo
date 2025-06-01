# Wertigo Authentication System

This document describes how to set up and use the authentication system for the Wertigo travel recommendation application.

## Setup Instructions

### Prerequisites

- MySQL 8.0+ server installed and running
- Python 3.8+ with pip

### Database Setup

1. Make sure your MySQL server is running.
2. Run the setup script to create the database and user:

   ```bash
   # On Windows
   setup_database.bat
   
   # On Unix/Linux/MacOS
   # First make the script executable
   chmod +x setup_database.sh
   # Then run it
   ./setup_database.sh
   ```

3. The script will prompt you for:
   - MySQL host (default: localhost)
   - MySQL admin username (default: root)
   - MySQL admin password

4. Alternatively, you can run the SQL script directly in MySQL Workbench:
   - Open MySQL Workbench
   - Connect to your MySQL server
   - Open the `setup_database.sql` file
   - Execute the script

### Environment Configuration

1. Copy the example environment file:

   ```bash
   cp env.example .env
   ```

2. Edit the `.env` file with your specific configuration:
   - Update database credentials if needed
   - Change the secret key for production environments

### Python Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

## API Endpoints

The authentication system provides the following endpoints:

### User Registration

```
POST /api/auth/register
Content-Type: application/json

{
  "username": "user123",
  "email": "user@example.com",
  "password": "securePassword123",
  "first_name": "John",  // Optional
  "last_name": "Doe"     // Optional
}
```

Response:
```json
{
  "success": true,
  "message": "User registered successfully",
  "user_id": 1
}
```

### User Login

```
POST /api/auth/login
Content-Type: application/json

{
  "username": "user123",  // Can be username or email
  "password": "securePassword123"
}
```

Response:
```json
{
  "success": true,
  "message": "Login successful",
  "session_id": "d84f9df2-9e92-4d0e-8b15-c4f979135e9c",
  "user": {
    "id": 1,
    "username": "user123",
    "email": "user@example.com"
  }
}
```

### User Logout

```
POST /api/auth/logout
Content-Type: application/json

{
  "session_id": "d84f9df2-9e92-4d0e-8b15-c4f979135e9c"  // Optional if using cookies
}
```

Response:
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

### Get User Profile

```
GET /api/auth/profile
X-Session-ID: d84f9df2-9e92-4d0e-8b15-c4f979135e9c  // Optional if using cookies
```

Response:
```json
{
  "success": true,
  "profile": {
    "id": 1,
    "username": "user123",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "created_at": "2023-06-01T12:00:00"
  }
}
```

### Update User Profile

```
PUT /api/auth/profile
X-Session-ID: d84f9df2-9e92-4d0e-8b15-c4f979135e9c  // Optional if using cookies
Content-Type: application/json

{
  "first_name": "Johnny",  // Optional
  "last_name": "Doe",      // Optional
  "email": "newemail@example.com",  // Optional
  "password": "newSecurePassword123"  // Optional
}
```

Response:
```json
{
  "success": true,
  "message": "Profile updated successfully"
}
```

### Validate Session

```
GET /api/auth/validate
X-Session-ID: d84f9df2-9e92-4d0e-8b15-c4f979135e9c  // Optional if using cookies
```

Response:
```json
{
  "success": true,
  "message": "Session is valid",
  "user": {
    "id": 1,
    "username": "user123",
    "email": "user@example.com"
  }
}
```

## Authentication Middleware

The system includes middleware functions for protecting routes:

### login_required

This middleware ensures that a user is authenticated before accessing protected routes.

Usage in route definitions:

```python
from middleware import login_required

@app.route('/api/protected-route', methods=['GET'])
@login_required
def protected_route(user_id, username, email):
    # The middleware adds user information to kwargs
    return jsonify({
        "message": f"Hello, {username}!",
        "email": email
    })
```

### admin_required

This middleware is for routes that require admin privileges.

Usage in route definitions:

```python
from middleware import admin_required

@app.route('/api/admin-route', methods=['GET'])
@admin_required
def admin_route(user_id, username, email):
    # Admin-only functionality
    return jsonify({
        "message": "Admin panel accessed"
    })
```

## Security Considerations

- Passwords are hashed using PBKDF2 with SHA-256
- User sessions expire after 24 hours by default
- All sensitive operations verify the user's session
- Input validation is performed on registration and profile updates

## Troubleshooting

If you encounter issues:

1. Check MySQL connection details in `.env` file
2. Ensure MySQL server is running
3. Verify that the wertigo_db database exists
4. Check application logs for specific error messages 