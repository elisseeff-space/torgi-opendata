#!/usr/bin/env python3
"""
Script to download missing NSI data files from torgi-portal
"""

import json
import os
import requests
import time
from datetime import datetime


def download_missing_nsi_files():
    """Download missing NSI files from the portal"""
    
    # Load the structure file to get all NSI types and their URLs
    structure_file = './masterdata/data-20220101T0000-20251222T0000-structure-20250101.json'

    with open(structure_file, 'r', encoding='utf-8') as f:
        structure_data = json.load(f)

    # Define the directory where files should be stored
    masterdata_dir = './masterdata/'
    
    # Create directory if it doesn't exist
    os.makedirs(masterdata_dir, exist_ok=True)

    for obj in structure_data.get('listObjects', []):
        nsi_type = obj.get('NSIType')
        href = obj.get('href')

        if nsi_type and href:
            # Extract filename from the href
            filename = href.split('/')[-1]
            local_file_path = f'{masterdata_dir}{filename}'
            
            # Check if file already exists
            if os.path.exists(local_file_path):
                print(f"File already exists: {filename}. Skipping download.")
                continue
            
            print(f"Attempting to download: {nsi_type} from {href}")
            
            try:
                # Try to download the file
                response = requests.get(href, timeout=30)
                
                if response.status_code == 200:
                    # Check if the response contains an error message
                    if '"error"' in response.text or 'не существует или недоступен' in response.text:
                        print(f"Downloaded file {filename} contains an error message. Skipping.")
                        # Don't save the error message as a file
                    else:
                        # Save the file
                        with open(local_file_path, 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        print(f"Successfully downloaded: {filename}")
                else:
                    print(f"Failed to download {filename}. Status code: {response.status_code}")
                    print(f"Response: {response.text[:200]}...")  # Show first 200 chars of response
                    
            except requests.exceptions.RequestException as e:
                print(f"Error downloading {filename}: {str(e)}")
            
            # Be respectful to the server - add a small delay
            time.sleep(1)


def main():
    print("Starting download of missing NSI files...")
    download_missing_nsi_files()
    print("Download process completed.")


if __name__ == '__main__':
    main()