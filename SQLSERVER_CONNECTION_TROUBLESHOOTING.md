# SQL Server Connection Troubleshooting Guide

## Common Issues and Solutions

### 1. Environment Variables Not Loading from .env File

**Problem**: The environment variables from the `.env` file are not being loaded properly, causing the application to use default values instead of the ones specified in the file.

**Solution**: 
- Check if environment variables are already set in your shell that might override the .env file
- Clear conflicting environment variables before running the application
- Use the helper script to troubleshoot: `python sqlserver_helper.py`

### 2. ODBC Driver Not Found

**Problem**: Error message: `Can't open lib 'ODBC Driver 17 for SQL Server' : file not found`

**Solution**: Install the Microsoft ODBC Driver for SQL Server:
- **Ubuntu/Debian**: `sudo apt-get install msodbcsql17`
- **CentOS/RHEL**: `sudo yum install msodbcsql17`
- **Arch Linux**: `sudo pacman -S msodbcsql17` or install from AUR

### 3. SQL Server Column Type Issues

**Problem**: Error message: `Column 'globalid' in table 'privatisationplans' is of a type that is invalid for use as a key column in an index`

**Solution**: 
- SQL Server doesn't allow indexing on `NVARCHAR(MAX)` columns
- Modified `db_utils.py` to convert `TEXT PRIMARY KEY` to `NVARCHAR(255) PRIMARY KEY` instead of `NVARCHAR(MAX)`
- Removed problematic foreign key constraints that referenced non-primary key columns

### 4. Foreign Key Constraint Issues

**Problem**: Error message: `There are no primary or candidate keys in the referenced table that match the referencing column list in the foreign key`

**Solution**: 
- Removed foreign key constraints that referenced columns that weren't primary keys
- This is acceptable for data import scenarios where referential integrity is maintained at the application level

## Usage Tips

### Setting Up SQL Server Connection

1. Ensure your `.env` file contains the correct values:
```
TORGIDB=SQLSERVER
SQL_SERVER=your-server-address
SQL_DATABASE=your-database-name
SQL_USERNAME=your-username
SQL_PASSWORD=your-password
SQL_DRIVER={ODBC Driver 17 for SQL Server}
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Install ODBC driver for your OS (see above)

4. Test the connection:
```bash
python sqlserver_helper.py
```

### Running the Application

Before running the main application, make sure to clear any conflicting environment variables:

```bash
# Clear environment variables and run
python -c "
import os
for var in ['TORGIDB', 'SQL_SERVER', 'SQL_DATABASE', 'SQL_USERNAME', 'SQL_PASSWORD', 'SQL_DRIVER']:
    if var in os.environ:
        del os.environ[var]
from dotenv import load_dotenv
load_dotenv()
# Now run your application code
"
```

Or use the uv command as intended:
```bash
uv run main.py --createdb
```

## Helper Scripts

- `sqlserver_helper.py` - Diagnoses and troubleshoots SQL Server connection issues
- `test_sqlserver_connection.py` - Basic connection test
- `debug_env.py` - Debug environment variable loading