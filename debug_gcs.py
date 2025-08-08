#!/usr/bin/env python3
"""
Debug script to understand GCS structure and fix model ingestion
"""

from google.cloud import storage
import os

def debug_gcs_structure():
    """Debug the GCS structure to understand the model folder layout"""
    client = storage.Client()
    bucket = client.bucket("pcc-datasets")
    
    print("=== GCS Structure Debug ===")
    
    # List all blobs with pcc-models prefix
    blobs = bucket.list_blobs(prefix="pcc-models")
    
    print("\nAll blobs with 'pcc-models' prefix:")
    for blob in blobs:
        print(f"  {blob.name}")
    
    print("\n=== Folder Analysis ===")
    
    # Re-list to analyze structure
    blobs = bucket.list_blobs(prefix="pcc-models")
    folders = []
    files = []
    
    for blob in blobs:
        if blob.name.endswith('/'):
            folders.append(blob.name)
        else:
            files.append(blob.name)
    
    print(f"\nFolders found: {len(folders)}")
    for folder in folders:
        print(f"  {folder}")
    
    print(f"\nFiles found: {len(files)}")
    for file in files[:10]:  # Show first 10 files
        print(f"  {file}")
    
    if len(files) > 10:
        print(f"  ... and {len(files) - 10} more files")
    
    # Analyze the structure
    print("\n=== Structure Analysis ===")
    
    # Group files by folder
    folder_files = {}
    for file in files:
        parts = file.split('/')
        if len(parts) >= 2:
            folder = '/'.join(parts[:-1]) + '/'
            if folder not in folder_files:
                folder_files[folder] = []
            folder_files[folder].append(parts[-1])
    
    print(f"\nFiles per folder:")
    for folder, files_list in folder_files.items():
        print(f"  {folder}: {len(files_list)} files")
        for file in files_list:
            print(f"    - {file}")

if __name__ == "__main__":
    debug_gcs_structure()
