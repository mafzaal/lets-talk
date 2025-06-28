#!/usr/bin/env python3
"""
Test script for collection management functionality.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from lets_talk.core.pipeline.services.vector_store_manager import (
    VectorStoreManager,
    check_collection_exists,
    create_collection_if_not_exists
)

def test_collection_management():
    """Test the collection management functionality."""
    
    # Test configuration (using local Qdrant for testing)
    storage_path = "./test_qdrant_db"
    collection_name = "test_collection"
    qdrant_url = ""  # Use local Qdrant
    embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
    
    print("Testing Collection Management Functionality")
    print("=" * 50)
    
    # Initialize manager
    manager = VectorStoreManager(
        storage_path=storage_path,
        collection_name=collection_name,
        qdrant_url=qdrant_url,
        embedding_model=embedding_model
    )
    
    # Test 1: Check if collection exists (should be False initially)
    print("1. Checking if collection exists...")
    exists = manager.collection_exists()
    print(f"   Collection exists: {exists}")
    
    # Test 2: Create collection
    print("2. Creating collection...")
    created = manager.create_collection()
    print(f"   Collection created: {created}")
    
    # Test 3: Check if collection exists again (should be True now)
    print("3. Checking if collection exists after creation...")
    exists_after = manager.collection_exists()
    print(f"   Collection exists: {exists_after}")
    
    # Test 4: Test convenience functions
    print("4. Testing convenience functions...")
    exists_conv = check_collection_exists(storage_path, collection_name, qdrant_url, embedding_model)
    print(f"   Collection exists (convenience function): {exists_conv}")
    
    created_conv = create_collection_if_not_exists(storage_path, collection_name, qdrant_url, embedding_model)
    print(f"   Create if not exists (convenience function): {created_conv}")
    
    # Test 5: Test load_vector_store with auto-creation
    print("5. Testing load_vector_store with auto-creation...")
    vector_store = manager.load_vector_store()
    print(f"   Vector store loaded: {vector_store is not None}")
    
    if vector_store and hasattr(vector_store, 'client'):
        vector_store.client.close()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    test_collection_management()
