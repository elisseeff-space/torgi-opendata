#!/usr/bin/env python3
"""
Module to create and populate master data tables from masterdata JSON files
"""

import json
import os
import sqlite3
import requests
import argparse
from datetime import datetime
import uuid


def create_nsi_tables():
    """Create NSI tables based on data-20220101T0000-20251222T0000-structure-20250101.json"""
    conn = sqlite3.connect('torgi.db')
    cursor = conn.cursor()
    
    # Load the structure file to get NSI types
    structure_file = './masterdata/data-20220101T0000-20251222T0000-structure-20250101.json'
    
    with open(structure_file, 'r', encoding='utf-8') as f:
        structure_data = json.load(f)
    
    for obj in structure_data.get('listObjects', []):
        nsi_type = obj.get('NSIType')
        href = obj.get('href')
        
        if nsi_type and href:
            # Process the data from local file (since online URLs may not be accessible)
            try:
                print(f"Processing NSI type: {nsi_type}")
                
                # Extract filename from the href
                filename = href.split('/')[-1]
                local_file_path = f'./masterdata/{filename}'
                
                # Check if local file exists before trying to load it
                if not os.path.exists(local_file_path):
                    print(f"Warning: Local file does not exist: {local_file_path}. Skipping NSI type: {nsi_type}")
                    continue
                
                # Load data from local file
                with open(local_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                export_obj = data.get('exportObject', {})
                structured_obj = export_obj.get('structuredObject', {})
                
                # Get the masterData object which contains the NSI array of items
                master_data = structured_obj.get('masterData', {})
                nsi_array = master_data.get('NSI', [])
                
                # Extract items for the specific NSI type from the NSI array
                nsi_items = []
                for item in nsi_array:
                    if nsi_type in item:
                        nsi_items.append(item[nsi_type])
                
                if not nsi_items:
                    print(f"No items found for NSI type: {nsi_type}")
                    continue
                
                # Create table for this NSI type with prefix nsi_
                table_name = f"nsi_{nsi_type}"
                
                # Build column list from first item's keys
                if nsi_items:
                    first_item = nsi_items[0]
                    columns = []
                    
                    # Add standard fields first
                    columns.append("globalid TEXT PRIMARY KEY")
                    columns.append("createdate TEXT")
                    columns.append("updatedate TEXT")
                    
                    # Add columns from the data, handling nested structures
                    for key, value in first_item.items():
                        if isinstance(value, dict):
                            # Handle nested dictionary - create flattened columns
                            for nested_key in value.keys():
                                col_name = f"{key}_{nested_key}"
                                columns.append(f"{col_name} TEXT")
                        elif isinstance(value, list):
                            # Handle top-level array fields - store as JSON string
                            columns.append(f"{key} TEXT")
                        else:
                            # Simple field
                            columns.append(f"{key} TEXT")
                    
                    # Create the table
                    create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
                    cursor.execute(create_table_sql)
                    
                    # Insert data into the table
                    for item in nsi_items:
                        global_id = str(uuid.uuid4())
                        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                        
                        # Prepare values for insertion
                        values = [global_id, now, now]  # globalid, createdate, updatedate
                        
                        # Add values for each column based on the first item structure
                        for key, value in first_item.items():
                            if isinstance(value, dict):
                                # Handle nested dictionary
                                for nested_key in value.keys():
                                    val = item.get(key, {}).get(nested_key)
                                    # Convert complex objects (dicts, lists) to JSON string for storage
                                    if isinstance(val, (dict, list)):
                                        val = json.dumps(val, ensure_ascii=False)
                                    values.append(val if val is not None else '')
                            elif isinstance(value, list):
                                # Handle top-level array fields by converting to JSON string
                                val = item.get(key)
                                if isinstance(val, (dict, list)):
                                    val = json.dumps(val, ensure_ascii=False)
                                values.append(val if val is not None else '')
                            else:
                                # Simple field
                                val = item.get(key)
                                # Convert complex objects (dicts, lists) to JSON string for storage
                                if isinstance(val, (dict, list)):
                                    val = json.dumps(val, ensure_ascii=False)
                                values.append(val if val is not None else '')
                        
                        # Build INSERT query
                        placeholders = ', '.join(['?' for _ in values])
                        insert_sql = f"INSERT OR REPLACE INTO {table_name} VALUES ({placeholders})"
                        cursor.execute(insert_sql, values)
                
            except Exception as e:
                print(f"Error processing NSI type {nsi_type} from {href}: {str(e)}")
                continue
    
    conn.commit()
    conn.close()


def main():
    parser = argparse.ArgumentParser(description='Handle master data tables')
    parser.add_argument('--createdb', action='store_true', help='Create NSI tables from master data')
    
    args = parser.parse_args()
    
    if args.createdb:
        print("Creating NSI tables...")
        create_nsi_tables()
        print("NSI tables created and populated successfully.")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()