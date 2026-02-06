#!/usr/bin/env python3
"""
Module to download files specified in meta.json from the privatisation plans section
"""

import json
import os
import requests
from urllib.parse import urlparse
import argparse


def download_file(url, dest_path):
    """Download a file from URL to destination path if it doesn't exist"""
    if os.path.exists(dest_path):
        print(f"File already exists: {dest_path}")
        return True
    
    try:
        print(f"Downloading {url}...")
        response = requests.get(url)
        response.raise_for_status()
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        with open(dest_path, 'wb') as f:
            f.write(response.content)
        
        print(f"Downloaded: {dest_path}")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return False


def download_meta_files():
    """Download all files specified in the meta.json file"""
    meta_file = './privatisationplans/meta.json'
    
    if not os.path.exists(meta_file):
        print(f"Meta file not found: {meta_file}")
        return
    
    with open(meta_file, 'r', encoding='utf-8') as f:
        meta_data = json.load(f)
    
    # Create loaded directory if it doesn't exist
    loaded_dir = './privatisationplans/loaded/'
    os.makedirs(loaded_dir, exist_ok=True)
    
    # Download data files
    data_sources = meta_data.get('data', [])
    print(f"Found {len(data_sources)} data sources to download")
    
    for item in data_sources:
        source_url = item.get('source')
        if source_url:
            # Extract filename from URL
            parsed_url = urlparse(source_url)
            filename = os.path.basename(parsed_url.path)
            dest_path = os.path.join(loaded_dir, filename)
            download_file(source_url, dest_path)
    
    # Download structure files
    structure_sources = meta_data.get('structure', [])
    print(f"Found {len(structure_sources)} structure sources to download")
    
    for item in structure_sources:
        source_url = item.get('source')
        if source_url:
            # Extract filename from URL
            parsed_url = urlparse(source_url)
            filename = os.path.basename(parsed_url.path)
            dest_path = os.path.join(loaded_dir, filename)
            download_file(source_url, dest_path)


def main():
    parser = argparse.ArgumentParser(description='Download files from meta.json')
    parser.add_argument('--download', action='store_true', help='Download files from meta.json')
    
    args = parser.parse_args()
    
    if args.download:
        download_meta_files()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()