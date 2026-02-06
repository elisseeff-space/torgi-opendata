#!/usr/bin/env python3
"""
Test script to verify the implemented functionality
"""

import subprocess
import sys
import os
import sqlite3
import pandas as pd


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
    
    # Check if database file was created
    if os.path.exists('torgi.db'):
        print("✓ Database file created successfully")
        
        # Connect to database and check tables
        conn = sqlite3.connect('torgi.db')
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables in database: {tables}")
        
        # Verify required tables exist
        required_tables = ['privatisationplans', 'privatisationplanlist', 'privatizationobjects']
        for table in required_tables:
            if (table,) in tables:
                print(f"✓ Table {table} exists")
            else:
                print(f"✗ Table {table} missing")
        
        conn.close()
    else:
        print("✗ Database file was not created")


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
        print("Loaded directory does not exist, attempting download...")
        result = subprocess.run([sys.executable, 'metadownload.py', '--download'], capture_output=True, text=True)
        print("Download result:", result.returncode)
        if result.stdout:
            print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)


def test_excel_export():
    """Test the Excel export functionality"""
    print("\nTesting Excel export...")
    
    # First, try to load some data if possible
    try:
        # Check if there's data to export
        conn = sqlite3.connect('torgi.db')
        cursor = conn.cursor()
        
        # Check if tables have data
        for table in ['privatisationplans', 'privatisationplanlist', 'privatizationobjects']:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"Records in {table}: {count}")
        
        conn.close()
        
        # Try to export to Excel
        result = subprocess.run([sys.executable, 'createexcel_privplans.py', '--export'], capture_output=True, text=True)
        print("Excel export result:", result.returncode)
        if result.stdout:
            print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Check if Excel file was created
        if os.path.exists('privatisation_plans_export.xlsx'):
            print("✓ Excel file created successfully")
        else:
            print("✗ Excel file was not created")
            
    except Exception as e:
        print(f"Error testing Excel export: {str(e)}")


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
        conn = sqlite3.connect('torgi.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        nsi_tables = [table[0] for table in tables if table[0].startswith('nsi_')]
        print(f"NSI tables created: {nsi_tables}")
        
        conn.close()
    except Exception as e:
        print(f"Error checking NSI tables: {str(e)}")


def main():
    print("Running functionality tests...\n")
    
    test_main_module()
    test_metadownload_module()
    test_excel_export()
    test_masterdata_module()
    
    print("\nFunctionality tests completed!")


if __name__ == '__main__':
    main()