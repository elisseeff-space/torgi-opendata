import os
import sqlite3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_db_connection():
    """
    Creates and returns a database connection based on the TORGIDB environment variable.
    If TORGIDB=SQLITE (default), returns a SQLite connection.
    If TORGIDB=SQLSERVER, returns a MS SQL Server connection.
    """
    db_type = os.getenv('TORGIDB', 'SQLITE').upper()
    
    if db_type == 'SQLITE':
        return sqlite3.connect('torgi.db')
    elif db_type == 'SQLSERVER':
        # Import pyodbc only when needed to avoid import errors when not available
        try:
            import pyodbc
        except ImportError:
            raise ImportError("pyodbc is required for SQL Server support. Install it with: pip install pyodbc")
        
        # Get SQL Server connection parameters from environment variables
        server = os.getenv('SQL_SERVER', 'localhost')
        database = os.getenv('SQL_DATABASE', 'torgi')
        username = os.getenv('SQL_USERNAME')
        password = os.getenv('SQL_PASSWORD')
        driver = os.getenv('SQL_DRIVER', '{ODBC Driver 17 for SQL Server}')
        
        if username and password:
            # Use SQL Server authentication
            conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        else:
            # Use Windows authentication
            conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes'
        
        return pyodbc.connect(conn_str)
    else:
        raise ValueError(f"Unsupported database type: {db_type}. Use 'SQLITE' or 'SQLSERVER'.")


def execute_query(query, params=None, fetch=False):
    """
    Executes a query using the appropriate database connection.
    Automatically handles differences between SQLite and SQL Server syntax.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Handle differences in SQL syntax between SQLite and SQL Server
    db_type = os.getenv('TORGIDB', 'SQLITE').upper()
    if db_type == 'SQLSERVER':
        # Convert SQLite-specific syntax to SQL Server compatible syntax
        # Replace "INSERT OR REPLACE" with SQL Server equivalent using IF EXISTS pattern
        if 'INSERT OR REPLACE' in query.upper():
            import re
            
            # Find the table name after INSERT OR REPLACE
            match = re.search(r'INSERT\s+OR\s+REPLACE\s+INTO\s+([^\s\(]+)', query, re.IGNORECASE)
            if match:
                table_name = match.group(1).strip('[]`"')  # Remove any quotes or brackets
                
                # For our specific use case, we know the structure: 
                # INSERT OR REPLACE INTO table VALUES (?, ?, ?, ...)
                # The first parameter is typically the primary key (globalid)
                
                # Count the number of parameters to determine how many placeholders we have
                values_match = re.search(r'VALUES\s*\((.*?)\)', query, re.IGNORECASE)
                if values_match:
                    placeholders_part = values_match.group(1)
                    # Count parameters by counting the '?' placeholders
                    param_count = placeholders_part.count('?')
                    
                    # For our use case, we know the first column is the primary key
                    # We'll create a generic approach that assumes the first param is the PK
                    pk_placeholder = '?'  # First placeholder is the primary key
                    other_placeholders = [f'? AS col{i+2}' for i in range(param_count-1)]  # Other columns
                    
                    # Create SQL Server equivalent: IF EXISTS UPDATE ELSE INSERT
                    # Build the SET clause for updates (all columns except the first one)
                    update_set_parts = []
                    for i in range(1, param_count):
                        update_set_parts.append(f"COL{i+1} = ?")
                    
                    # Since we don't know the actual column names here, we'll use a different approach
                    # We'll create a more generic solution that works with the known structure
                    # In our case, the first column is always the primary key (globalid)
                    
                    # Create a simplified query assuming we know the first column is the primary key
                    # We'll use a more direct approach - get the actual column names from the table
                    try:
                        # Get the actual column names from the table schema
                        import pyodbc
                        temp_conn = get_db_connection()
                        temp_cursor = temp_conn.cursor()
                        
                        # Get column names for this table
                        temp_cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}' ORDER BY ORDINAL_POSITION")
                        columns_info = temp_cursor.fetchall()
                        actual_cols = [row[0] for row in columns_info]
                        
                        temp_conn.close()
                        
                        # Now we can build the proper query
                        pk_col = actual_cols[0]  # First column is primary key
                        update_cols = actual_cols[1:]  # Remaining columns
                        
                        # Build the UPDATE SET clause
                        update_set_clause = ', '.join([f"[{col}] = ?" for col in update_cols])
                        
                        # Use MERGE statement which is cleaner for UPSERT operations in SQL Server
                        # MERGE requires constructing source data inline
                        # Create a VALUES clause that represents the incoming data
                        values_list = [f'?' for _ in actual_cols]  # Same number of ? as columns
                        values_clause = f"({', '.join(values_list)})"
                        
                        query = f"""
MERGE [{table_name}] AS target
USING (VALUES {values_clause}) AS source ({', '.join([f'[{col}]' for col in actual_cols])})
ON target.[{pk_col}] = source.[{pk_col}]
WHEN MATCHED THEN
    UPDATE SET {update_set_clause}
WHEN NOT MATCHED THEN
    INSERT ({', '.join([f'[{col}]' for col in actual_cols])})
    VALUES ({', '.join([f'source.[{col}]' for col in actual_cols])});
"""
                        # For MERGE, we need to duplicate the non-PK parameters for the UPDATE SET clause
                        # Original params: [pk, val1, val2, ..., valN-1] (N params)
                        # Query needs: N params for VALUES + (N-1) params for UPDATE SET = 2N-1 params
                        # New params: [pk, val1, val2, ..., valN-1, val1, val2, ..., valN-1]
                        if params:
                            pk_val = params[0]
                            non_pk_params = params[1:]  # All params except the primary key
                            # Extend params with non-PK params again for the UPDATE SET clause
                            params = params + non_pk_params  # [original_params..., non_pk_params...]
                            
                    except Exception as e:
                        # If we can't get column names, fall back to original query
                        # This shouldn't happen in practice since we create the tables ourselves
                        print(f"Warning: Could not get column names for table {table_name}: {str(e)}")
                        pass

    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        if fetch:
            result = cursor.fetchall()
            return result
        else:
            conn.commit()
            return cursor
    finally:
        conn.close()


def create_table_sqlite_to_sqlserver(sqlite_sql):
    """
    Converts SQLite CREATE TABLE statements to SQL Server compatible syntax.
    """
    db_type = os.getenv('TORGIDB', 'SQLITE').upper()
    
    if db_type == 'SQLSERVER':
        # Import pyodbc only when needed to avoid import errors when not available
        try:
            import pyodbc
        except ImportError:
            # If pyodbc is not available, return the original SQLite SQL
            return sqlite_sql
        
        # Convert SQLite-specific syntax to SQL Server
        sql_server_sql = sqlite_sql

        # Replace AUTOINCREMENT with IDENTITY
        sql_server_sql = sql_server_sql.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'INT IDENTITY(1,1) PRIMARY KEY')

        # Handle TEXT columns - for PRIMARY KEY columns use NVARCHAR(255), for others use NVARCHAR(MAX)
        # SQL Server doesn't allow indexing on NVARCHAR(MAX) columns
        import re
        
        # First, handle PRIMARY KEY TEXT columns (replace with NVARCHAR(255))
        sql_server_sql = re.sub(r'TEXT\s+PRIMARY\s+KEY', 'NVARCHAR(255) PRIMARY KEY', sql_server_sql, flags=re.IGNORECASE)
        
        # Then handle other TEXT columns (replace with NVARCHAR(MAX))
        sql_server_sql = sql_server_sql.replace('TEXT', 'NVARCHAR(MAX)')
        
        # Replace 'IF NOT EXISTS' which is SQLite-specific
        # For SQL Server, we need to check if table exists before creating
        sql_server_sql = sql_server_sql.replace('CREATE TABLE IF NOT EXISTS', 'CREATE TABLE')
        
        # For SQL Server, we need to wrap the CREATE TABLE in a conditional check
        table_name_start = sqlite_sql.find('TABLE IF NOT EXISTS ') + len('TABLE IF NOT EXISTS ')
        table_name_end = sqlite_sql.find(' (', table_name_start)
        if table_name_start != -1 and table_name_end != -1:
            table_name = sqlite_sql[table_name_start:table_name_end].strip()
            # Return a conditional CREATE statement for SQL Server
            conditional_create = f"""
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{table_name}' AND xtype='U')
BEGIN
    {sql_server_sql}
END
"""
            return conditional_create
        else:
            return sql_server_sql
    else:
        return sqlite_sql