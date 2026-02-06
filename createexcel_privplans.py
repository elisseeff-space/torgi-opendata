#!/usr/bin/env python3
"""
Module to export privatisation plans data to Excel sheets
"""

import sqlite3
import pandas as pd
import argparse
from pathlib import Path


def export_to_excel():
    """Export privatisation plans data to Excel with separate sheets"""
    conn = sqlite3.connect('torgi.db')
    
    # Read data from tables
    privatisation_plans_df = pd.read_sql_query("SELECT * FROM privatisationplans", conn)
    privatisation_planlist_df = pd.read_sql_query("SELECT * FROM privatisationplanlist", conn)
    privatization_objects_df = pd.read_sql_query("SELECT * FROM privatizationobjects", conn)
    
    conn.close()
    
    # Export to Excel with separate sheets
    excel_filename = 'privatisation_plans_export.xlsx'
    
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        privatisation_plans_df.to_excel(writer, sheet_name='privatisationplans', index=False)
        privatisation_planlist_df.to_excel(writer, sheet_name='privatisationplanlist', index=False)
        privatization_objects_df.to_excel(writer, sheet_name='privatizationobjects', index=False)
    
    print(f"Data exported to {excel_filename}")


def main():
    parser = argparse.ArgumentParser(description='Export privatisation plans data to Excel')
    parser.add_argument('--export', action='store_true', help='Export data to Excel')
    
    args = parser.parse_args()
    
    if args.export:
        export_to_excel()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()