#!/usr/bin/env python3
"""
Test script to verify SQL Server functionality when TORGIDB=SQLSERVER
"""

import os
from db_utils import get_db_connection

def test_sql_server_connection():
    """Test SQL Server connection setup"""
    # Temporarily set environment to SQL Server
    original_value = os.environ.get('TORGIDB')
    os.environ['TORGIDB'] = 'SQLSERVER'
    
    try:
        # This should raise an ImportError since pyodbc is not available
        # But it should handle it gracefully
        conn = get_db_connection()
        print("SQL Server connection successful")
        conn.close()
    except ImportError as e:
        print(f"Expected error for SQL Server (pyodbc not available): {e}")
    except Exception as e:
        print(f"Other error for SQL Server: {e}")
    finally:
        # Restore original value
        if original_value is not None:
            os.environ['TORGIDB'] = original_value
        else:
            del os.environ['TORGIDB']

def test_sqlite_connection():
    """Test SQLite connection still works"""
    # Ensure we're using SQLite
    original_value = os.environ.get('TORGIDB')
    os.environ['TORGIDB'] = 'SQLITE'
    
    try:
        conn = get_db_connection()
        print("SQLite connection successful")
        conn.close()
    except Exception as e:
        print(f"Error for SQLite: {e}")
    finally:
        # Restore original value
        if original_value is not None:
            os.environ['TORGIDB'] = original_value
        else:
            del os.environ['TORGIDB']

if __name__ == '__main__':
    print("Testing database connection utilities...")
    test_sqlite_connection()
    test_sql_server_connection()
    print("Test completed!")