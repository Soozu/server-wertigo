#!/usr/bin/env python3
"""
Database Initialization Script for WerTigo Trip Planner
"""

import os
import sys
from db import create_tables, get_connection, execute_query
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    
    conn = get_connection()
    if conn:
        print("✅ Database connection successful!")
        conn.close()
        return True
    else:
        print("❌ Database connection failed!")
        return False

def initialize_database():
    """Initialize database tables"""
    print("🏗️  Creating database tables...")
    
    try:
        create_tables()
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def show_table_info():
    """Show information about created tables"""
    print("📊 Checking created tables...")
    
    tables_query = """
    SELECT TABLE_NAME as table_name
    FROM information_schema.tables 
    WHERE table_schema = DATABASE()
    ORDER BY TABLE_NAME
    """
    
    try:
        tables = execute_query(tables_query)
        if tables:
            print("📋 Created tables:")
            for table in tables:
                table_name = table['table_name']
                print(f"   • {table_name}")
                
                # Get column info
                columns_query = f"""
                SELECT COLUMN_NAME as column_name, DATA_TYPE as data_type, 
                       IS_NULLABLE as is_nullable, COLUMN_DEFAULT as column_default
                FROM information_schema.columns 
                WHERE table_schema = DATABASE() AND TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
                """
                
                columns = execute_query(columns_query)
                if columns:
                    for col in columns[:3]:  # Show first 3 columns
                        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                        default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                        print(f"     - {col['column_name']}: {col['data_type']} {nullable}{default}")
                    if len(columns) > 3:
                        print(f"     ... and {len(columns) - 3} more columns")
                print()
        else:
            print("❌ No tables found!")
    except Exception as e:
        print(f"❌ Error checking tables: {e}")

def create_test_trip():
    """Create a test trip to verify functionality"""
    print("🧪 Creating test trip...")
    
    try:
        import uuid
        from datetime import datetime
        
        # Import the database functions
        from db import create_trip_db, get_trip_db, add_destination_to_trip_db
        
        # Create test trip
        trip_id = str(uuid.uuid4())
        trip_data = {
            'trip_name': 'Test Trip',
            'destination': 'Philippines',
            'budget': 10000,
            'travelers': 2
        }
        
        success = create_trip_db(trip_id, None, 'test_session', trip_data)
        
        if success:
            print(f"✅ Test trip created with ID: {trip_id}")
            
            # Add a test destination
            destination_data = {
                'name': 'Boracay Beach',
                'city': 'Malay',
                'province': 'Aklan',
                'description': 'Beautiful white sand beach',
                'category': 'Beach',
                'rating': 4.5,
                'budget': 2000,
                'latitude': 11.9674,
                'longitude': 121.9248
            }
            
            dest_id = add_destination_to_trip_db(trip_id, destination_data)
            if dest_id:
                print(f"✅ Test destination added with ID: {dest_id}")
            
            # Retrieve the trip to verify
            retrieved_trip = get_trip_db(trip_id, None, 'test_session')
            if retrieved_trip:
                print("✅ Trip retrieval successful!")
                print(f"   Trip: {retrieved_trip['trip_name']}")
                print(f"   Destinations: {len(retrieved_trip['destinations'])}")
                return trip_id
            else:
                print("❌ Failed to retrieve test trip")
        else:
            print("❌ Failed to create test trip")
            
    except Exception as e:
        print(f"❌ Error creating test trip: {e}")
        import traceback
        traceback.print_exc()
    
    return None

def cleanup_test_data(trip_id):
    """Clean up test data"""
    if trip_id:
        print("🧹 Cleaning up test data...")
        try:
            # Delete test trip
            delete_query = "DELETE FROM trips WHERE id = %s"
            execute_query(delete_query, (trip_id,), fetch=False)
            print("✅ Test data cleaned up")
        except Exception as e:
            print(f"❌ Error cleaning up test data: {e}")

def main():
    """Main function"""
    print("=" * 60)
    print("🌟 WerTigo Trip Planner - Database Initialization")
    print("=" * 60)
    
    # Test connection
    if not test_connection():
        print("\n❌ Cannot proceed without database connection.")
        print("Please check your database configuration in .env file:")
        print("   DB_HOST=localhost")
        print("   DB_USER=wertigo_user") 
        print("   DB_PASSWORD=wertigo_password")
        print("   DB_NAME=wertigo_db")
        print("   DB_PORT=3306")
        sys.exit(1)
    
    print()
    
    # Initialize tables
    if not initialize_database():
        print("\n❌ Failed to initialize database tables.")
        sys.exit(1)
    
    print()
    
    # Show table info
    show_table_info()
    
    # Create and test a trip
    trip_id = create_test_trip()
    
    print()
    
    # Cleanup
    cleanup_test_data(trip_id)
    
    print("=" * 60)
    print("🎉 Database initialization completed successfully!")
    print("🚀 You can now start the Flask server with: python run_server.py")
    print("=" * 60)

if __name__ == '__main__':
    main() 