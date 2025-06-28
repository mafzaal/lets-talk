#!/usr/bin/env python3
import tempfile
import os
import time
import sys
import shutil

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

from lets_talk.core.pipeline.services.metadata_manager import BackupManager

def test_backup_debug():
    # Create temp file
    temp_dir = tempfile.mkdtemp()
    test_file = os.path.join(temp_dir, 'test.txt')
    
    # Write original content
    with open(test_file, 'w') as f:
        f.write('Original content')
    
    print('Original file content:')
    with open(test_file, 'r') as f:
        content = f.read()
        print(repr(content))
    
    # Create backup
    manager = BackupManager()
    backup_path = manager.create_backup(test_file)
    print(f'Backup created at: {backup_path}')
    
    # Check backup content immediately
    print('Backup content immediately after creation:')
    if backup_path and os.path.exists(backup_path):
        with open(backup_path, 'r') as f:
            backup_content = f.read()
            print(repr(backup_content))
    else:
        print('Backup file not found!')
    
    # Modify original
    with open(test_file, 'w') as f:
        f.write('Modified content')
    
    print('\nModified file content:')
    with open(test_file, 'r') as f:
        content = f.read()
        print(repr(content))
    
    print('Backup content after modification:')
    if backup_path and os.path.exists(backup_path):
        with open(backup_path, 'r') as f:
            backup_content = f.read()
            print(repr(backup_content))
    else:
        print('Backup file not found!')
    
    # Clean up
    shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    test_backup_debug()
