#!/usr/bin/env python3
"""
Helper script to manage SQL Server connections and troubleshoot common issues
"""

import os
import sys
from dotenv import load_dotenv
import pyodbc

def load_environment_variables():
    """Clear any conflicting environment variables and load from .env file"""
    # Clear environment variables that might interfere
    for var in ['TORGIDB', 'SQL_SERVER', 'SQL_DATABASE', 'SQL_USERNAME', 'SQL_PASSWORD', 'SQL_DRIVER']:
        if var in os.environ:
            del os.environ[var]

    # Load from .env file
    load_dotenv()
    
    print("Environment variables loaded from .env file:")
    for var in ['TORGIDB', 'SQL_SERVER', 'SQL_DATABASE', 'SQL_USERNAME', 'SQL_PASSWORD', 'SQL_DRIVER']:
        value = os.getenv(var)
        if var == 'SQL_PASSWORD':
            print(f"  {var}: {'***' if value else 'None'}")
        else:
            print(f"  {var}: {value}")

def test_connection():
    """Test the SQL Server connection"""
    server = os.getenv('SQL_SERVER')
    database = os.getenv('SQL_DATABASE')
    username = os.getenv('SQL_USERNAME')
    password = os.getenv('SQL_PASSWORD')
    driver = os.getenv('SQL_DRIVER')

    if not all([server, database, username, password, driver]):
        print("ERROR: Missing required environment variables for SQL Server connection")
        return False

    if username and password:
        # Use SQL Server authentication
        conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        print("Using SQL Server authentication")
    else:
        # Use Windows authentication
        conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes'
        print("Using Windows authentication - this may not work on Linux")

    print(f"Connection String: {conn_str}")

    try:
        print("Attempting to connect to SQL Server...")
        conn = pyodbc.connect(conn_str)
        print("✓ Connection successful!")
        
        # Test with a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        row = cursor.fetchone()
        print(f"SQL Server Version: {row[0][:50]}...")
        
        conn.close()
        print("✓ Connection closed successfully.")
        return True
    except Exception as e:
        print(f"✗ Connection failed: {str(e)}")
        return False

def check_odbc_drivers():
    """Check available ODBC drivers"""
    print("\nAvailable ODBC drivers:")
    for driver in pyodbc.drivers():
        print(f"  - {driver}")
    
    required_driver = os.getenv('SQL_DRIVER', '{ODBC Driver 17 for SQL Server}')
    if required_driver.strip('{}') in [d for d in pyodbc.drivers()]:
        print(f"✓ Required driver '{required_driver}' is available")
        return True
    else:
        print(f"✗ Required driver '{required_driver}' is NOT available")
        print("You may need to install the Microsoft ODBC Driver for SQL Server")
        return False

def main():
    print("SQL Server Connection Troubleshooter")
    print("=" * 40)
    
    # Load environment variables
    load_environment_variables()
    
    # Check ODBC drivers
    drivers_available = check_odbc_drivers()
    
    if not drivers_available:
        print("\nPlease install the Microsoft ODBC Driver for SQL Server:")
        print("- On Ubuntu/Debian: sudo apt-get install msodbcsql17")
        print("- On CentOS/RHEL: sudo yum install msodbcsql17")
        print("- On Arch Linux: sudo pacman -S msodbcsql17 or use AUR")
        return 1
    
    # Test connection
    connection_successful = test_connection()
    
    if connection_successful:
        print("\n✓ SQL Server connection is working properly!")
        return 0
    else:
        print("\n✗ SQL Server connection failed.")
        print("\nTroubleshooting tips:")
        print("1. Verify your .env file contains correct credentials")
        print("2. Check that the SQL Server is accessible from your network")
        print("3. Ensure the firewall allows connections to the SQL Server port (usually 1433)")
        print("4. Confirm the database name and user permissions are correct")
        return 1

if __name__ == "__main__":
    sys.exit(main())