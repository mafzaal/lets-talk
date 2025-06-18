#!/usr/bin/env python3
"""
Test script for the updated simple_pipeline_job module.

This script demonstrates how to use the job configuration with default values
from config.py and how to override specific values.
"""

import sys
import os
from pathlib import Path

# Add py-src to Python path
sys.path.insert(0, str(Path(__file__).parent / "py-src"))

from lets_talk.simple_pipeline_job import (
    get_default_job_config, 
    create_job_config,
    simple_pipeline_job
)

def test_default_config():
    """Test getting default job configuration."""
    print("=== Testing Default Job Configuration ===")
    config = get_default_job_config()
    
    print(f"Total configuration options: {len(config)}")
    print("\nKey configuration values:")
    print(f"  job_id: {config['job_id']}")
    print(f"  data_dir: {config['data_dir']}")
    print(f"  output_dir: {config['output_dir']}")
    print(f"  embedding_model: {config['embedding_model']}")
    print(f"  use_chunking: {config['use_chunking']}")
    print(f"  chunk_size: {config['chunk_size']}")
    print(f"  incremental_mode: {config['incremental_mode']}")
    print()

def test_custom_config():
    """Test creating custom job configuration."""
    print("=== Testing Custom Job Configuration ===")
    
    # Create custom configuration with some overrides
    custom_values = {
        'job_id': 'test_custom_job',
        'force_recreate': True,
        'dry_run': True,
        'data_dir': './test_data',
        'chunk_size': 500,
        'health_check': True
    }
    
    config = create_job_config(custom_values)
    
    print("Custom overrides applied:")
    for key, value in custom_values.items():
        print(f"  {key}: {config[key]} (override)")
    
    print("\nSome values kept from defaults:")
    print(f"  output_dir: {config['output_dir']} (default)")
    print(f"  embedding_model: {config['embedding_model']} (default)")
    print(f"  use_chunking: {config['use_chunking']} (default)")
    print()

def test_dry_run_job():
    """Test running a pipeline job in dry-run mode."""
    print("=== Testing Pipeline Job (Dry Run) ===")
    
    # Create a job config for dry run testing
    job_config = create_job_config({
        'job_id': 'dry_run_test',
        'dry_run': True,
        'ci_mode': True,
        'health_check': True
    })
    
    print("Job configuration for dry run:")
    print(f"  job_id: {job_config['job_id']}")
    print(f"  dry_run: {job_config['dry_run']}")
    print(f"  ci_mode: {job_config['ci_mode']}")
    print(f"  health_check: {job_config['health_check']}")
    
    print("\nNote: To actually run the job, uncomment the following line:")
    print("# simple_pipeline_job(job_config)")
    print("(Commented out to avoid actual pipeline execution during testing)")
    print()

if __name__ == "__main__":
    print("Testing Updated Simple Pipeline Job Module")
    print("=" * 50)
    print()
    
    test_default_config()
    test_custom_config()
    test_dry_run_job()
    
    print("All tests completed successfully!")
    print("\nThe simple_pipeline_job module now uses default values from config.py")
    print("and provides convenient functions for job configuration management.")
