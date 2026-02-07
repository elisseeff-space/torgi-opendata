#!/usr/bin/env python3
"""
Simple test script to verify the implemented functionality without external dependencies
"""

import subprocess
import sys
import os
from db_utils import get_db_connection


def test_main_module():
    """Test the main module functionality"""
    print("Testing main module...")

    # Test creating database
    result = subprocess.run([sys.executable, 'main.py', '--createdb'], capture_output=True, text=True)
    print("Database creation result:", result.returncode)
    if result.stdout:
        print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    # Check if database file was created (for SQLite) or connection works (for SQL Server)
    db_type = os.getenv('TORGIDB', 'SQLITE').upper()
    if db_type == 'SQLITE':
        db_exists = os.path.exists('torgi.db')
    else:
        # For SQL Server, just test if we can connect
        try:
            conn = get_db_connection()
            conn.close()
            db_exists = True
        except:
            db_exists = False

    if db_exists:
        print("✓ Database connection successful")

        # Connect to database and check tables
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get list of tables (different query for SQL Server)
        if db_type == 'SQLSERVER':
            cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        else:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            
        tables = cursor.fetchall()
        print(f"Tables in database: {tables}")

        # Verify required tables exist
        required_tables = ['privatisationplans', 'privatisationplanlist', 'privatizationobjects']
        for table in required_tables:
            if (table,) in [t for t in tables]:
                print(f"✓ Table {table} exists")
            else:
                print(f"✗ Table {table} missing")

        conn.close()
    else:
        print("✗ Database connection failed")


def test_metadownload_module():
    """Test the metadownload module"""
    print("\nTesting metadownload module...")
    
    # Check if the loaded directory exists in privatisation plans
    loaded_dir = './privatisationplans/loaded/'
    if os.path.exists(loaded_dir):
        files = os.listdir(loaded_dir)
        print(f"Files in loaded directory: {files[:5]}...")  # Show first 5 files
        print(f"Total files in loaded directory: {len(files)}")
    else:
        print("Loaded directory does not exist, functionality needs to be tested separately")


def test_masterdata_module():
    """Test the masterdata module"""
    print("\nTesting masterdata module...")

    result = subprocess.run([sys.executable, 'masterdata.py', '--createdb'], capture_output=True, text=True)
    print("Masterdata creation result:", result.returncode)
    if result.stdout:
        print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    # Check if NSI tables were created
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get list of tables (different query for SQL Server)
        db_type = os.getenv('TORGIDB', 'SQLITE').upper()
        if db_type == 'SQLSERVER':
            cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        else:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            
        tables = cursor.fetchall()

        nsi_tables = [table[0] for table in [t[0] for t in tables] if table[0].startswith('nsi_')]
        print(f"NSI tables created: {nsi_tables}")

        conn.close()
    except Exception as e:
        print(f"Error checking NSI tables: {str(e)}")


def main():
    print("Running functionality tests...\n")
    
    test_main_module()
    test_metadownload_module()
    test_masterdata_module()
    
    print("\nFunctionality tests completed!")


if __name__ == '__main__':
    main()