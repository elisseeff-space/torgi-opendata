#!/usr/bin/env python3
"""
Main module for downloading and processing open data from torgi.gov.ru
"""

import argparse
import os
import sys
import sqlite3
from datetime import datetime
import json
import uuid
import requests
from urllib.parse import urljoin


def create_database():
    """Create SQLite database with required tables"""
    conn = sqlite3.connect('torgi.db')
    cursor = conn.cursor()
    
    # Create privatisationplans table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS privatisationplans (
            globalid TEXT PRIMARY KEY,
            createdate TEXT,
            updatedate TEXT,
            regnum TEXT NOT NULL,
            hostingorg TEXT,
            bidderorgcode TEXT,
            documenttype TEXT,
            publishdate TEXT,
            href TEXT
        )
    ''')
    
    # Create privatisationplanlist table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS privatisationplanlist (
            globalid TEXT PRIMARY KEY,
            createdate TEXT,
            updatedate TEXT,
            regnum TEXT,
            plan_number TEXT,
            plan_name TEXT,
            publish_date TEXT,
            signing_date TEXT,
            planing_period TEXT,
            org_code TEXT,
            org_name TEXT,
            org_inn TEXT,
            org_kpp TEXT,
            org_ogrn TEXT,
            org_type TEXT,
            budget_code TEXT,
            budget_name TEXT,
            authority TEXT,
            sum_first_year TEXT,
            sum_second_year TEXT,
            sum_third_year TEXT,
            FOREIGN KEY (regnum) REFERENCES privatisationplans (regnum)
        )
    ''')
    
    # Create privatizationobjects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS privatizationobjects (
            globalid TEXT PRIMARY KEY,
            createdate TEXT,
            updatedate TEXT,
            id TEXT,
            object_number TEXT,
            status_object TEXT,
            name TEXT,
            type TEXT,
            timing TEXT,
            subject_rf_code TEXT,
            subject_rf_name TEXT,
            location TEXT,
            purpose_code TEXT,
            purpose_name TEXT,
            kad_number TEXT,
            FOREIGN KEY (id) REFERENCES privatisationplanlist (regnum)
        )
    ''')
    
    conn.commit()
    conn.close()


def load_privatisation_data():
    """Load privatisation data from JSON files into database tables"""
    conn = sqlite3.connect('torgi.db')
    cursor = conn.cursor()
    
    # Load data from privatisationplans data files
    priv_dir = './privatisationplans/'
    for filename in os.listdir(priv_dir):
        if filename.startswith('data-') and filename.endswith('.json'):
            filepath = os.path.join(priv_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                for obj in data.get('listObjects', []):
                    global_id = str(uuid.uuid4())
                    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                    
                    # Insert into privatisationplans table
                    cursor.execute('''
                        INSERT OR REPLACE INTO privatisationplans
                        (globalid, createdate, updatedate, regnum, hostingorg, bidderorgcode, documenttype, publishdate, href)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        global_id, now, now,
                        obj.get('regNum'),
                        obj.get('hostingOrg'),
                        obj.get('bidderOrgCode'),
                        obj.get('documentType'),
                        obj.get('publishDate'),
                        obj.get('href')
                    ))
    
    conn.commit()
    conn.close()


def download_and_process_document(href_url, reg_num):
    """Download and process individual document from href"""
    try:
        response = requests.get(href_url)
        response.raise_for_status()
        
        doc_data = response.json()
        export_obj = doc_data.get('exportObject', {})
        structured_obj = export_obj.get('structuredObject', {})
        
        conn = sqlite3.connect('torgi.db')
        cursor = conn.cursor()
        
        # Process different types of documents
        if 'privatizationPlan' in structured_obj:
            plan_data = structured_obj['privatizationPlan']
            
            global_id = str(uuid.uuid4())
            now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            
            common_info = plan_data.get('commonInfo', {})
            hosting_org = plan_data.get('hostingOrg', {})
            planing_period = plan_data.get('planingPeriodInfo', {})
            budget_revenue = plan_data.get('budgetRevenueForecast', {})
            
            # Insert into privatisationplanlist table
            cursor.execute('''
                INSERT OR REPLACE INTO privatisationplanlist
                (globalid, createdate, updatedate, regnum, plan_number, plan_name, 
                publish_date, signing_date, planing_period, org_code, org_name, 
                org_inn, org_kpp, org_ogrn, org_type, budget_code, budget_name, 
                authority, sum_first_year, sum_second_year, sum_third_year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                global_id, now, now, reg_num,
                common_info.get('planNumber'),
                common_info.get('name'),
                common_info.get('publishDate'),
                planing_period.get('signingDate'),
                planing_period.get('planingPeriod'),
                hosting_org.get('code'),
                hosting_org.get('name'),
                hosting_org.get('INN'),
                hosting_org.get('KPP'),
                hosting_org.get('OGRN'),
                hosting_org.get('orgType'),
                plan_data.get('budget', {}).get('code'),
                plan_data.get('budget', {}).get('name'),
                plan_data.get('authority'),
                budget_revenue.get('sumFirstYear'),
                budget_revenue.get('sumSecondYear'),
                budget_revenue.get('sumThirdYear')
            ))
            
            # Process privatization objects
            for obj in plan_data.get('privatizationObjects', []):
                obj_global_id = str(uuid.uuid4())
                
                subject_rf = obj.get('subjectRF', {})
                purpose = obj.get('purpose', {})
                
                cursor.execute('''
                    INSERT OR REPLACE INTO privatizationobjects
                    (globalid, createdate, updatedate, id, object_number, status_object, 
                    name, type, timing, subject_rf_code, subject_rf_name, location, 
                    purpose_code, purpose_name, kad_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    obj_global_id, now, now, reg_num,
                    obj.get('objectNumber'),
                    obj.get('statusObject'),
                    obj.get('name'),
                    obj.get('type'),
                    obj.get('timing'),
                    subject_rf.get('code'),
                    subject_rf.get('name'),
                    obj.get('location'),
                    purpose.get('code'),
                    purpose.get('name'),
                    obj.get('kadNumber')
                ))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error processing document {href_url}: {str(e)}")


def process_all_documents():
    """Process all documents referenced in the privatisation plans"""
    conn = sqlite3.connect('torgi.db')
    cursor = conn.cursor()
    
    # Get all records with href from privatisationplans
    cursor.execute("SELECT regnum, href FROM privatisationplans WHERE href IS NOT NULL")
    records = cursor.fetchall()
    
    for reg_num, href in records:
        print(f"Processing document for regnum: {reg_num}")
        download_and_process_document(href, reg_num)
    
    conn.close()


def main():
    parser = argparse.ArgumentParser(description='Download and process open data from torgi.gov.ru')
    parser.add_argument('--createdb', action='store_true', help='Create database tables')
    parser.add_argument('--privplansupload', action='store_true', help='Upload privatisation plans data')
    parser.add_argument('--processdocs', action='store_true', help='Process document files')
    
    args = parser.parse_args()
    
    # Create database if requested
    if args.createdb:
        print("Creating database tables...")
        create_database()
        print("Database tables created successfully.")
    
    # Upload privatisation plans data if requested
    if args.privplansupload:
        print("Loading privatisation data...")
        load_privatisation_data()
        print("Privatisation data loaded successfully.")
    
    # Process document files if requested
    if args.processdocs:
        print("Processing document files...")
        process_all_documents()
        print("Document files processed successfully.")
    
    # If no arguments provided, show help
    if not any([args.createdb, args.privplansupload, args.processdocs]):
        parser.print_help()


if __name__ == '__main__':
    main()
