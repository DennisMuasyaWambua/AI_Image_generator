#!/usr/bin/env python3
"""
ChromaDB Test Script
This script tests the ChromaDB memory manager functionality.
"""

import os
import sys
import logging
from datastore.chroma_memory import ChromaMemoryManager

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_chromadb():
    """Test ChromaDB functionality"""
    print("Testing ChromaDB Memory Manager...")
    
    # Initialize ChromaDB memory manager
    memory_manager = ChromaMemoryManager()
    
    # Add some test data
    test_items = [
        {
            "prompt": "green dragon in a magical forest with emerald scales",
            "expanded_prompt": "a majestic dragon with green emerald scales in an enchanted forest with glowing mushrooms",
            "image_path": "/home/dennis/Desktop/ai-test/app/output/image_test1.png",
            "model_path": "/home/dennis/Desktop/ai-test/app/output/model_test1.obj",
            "tags": ["dragon", "green", "forest", "magical"]
        },
        {
            "prompt": "blue ice dragon on a mountain peak",
            "expanded_prompt": "a fearsome blue dragon with ice crystals on a snowy mountain peak",
            "image_path": "/home/dennis/Desktop/ai-test/app/output/image_test2.png",
            "model_path": "/home/dennis/Desktop/ai-test/app/output/model_test2.obj",
            "tags": ["dragon", "blue", "ice", "mountain"]
        },
        {
            "prompt": "fire dragon breathing flames",
            "expanded_prompt": "a powerful red dragon breathing bright orange flames against a dark sky",
            "image_path": "/home/dennis/Desktop/ai-test/app/output/image_test3.png",
            "model_path": "/home/dennis/Desktop/ai-test/app/output/model_test3.obj",
            "tags": ["dragon", "fire", "red", "flames"]
        }
    ]
    
    # Store test items
    print("\nStoring test items in ChromaDB...")
    for item in test_items:
        memory_manager.store(
            item["prompt"],
            item["expanded_prompt"],
            item["image_path"],
            item["model_path"],
            item["tags"]
        )
    
    # Test semantic search
    print("\nTesting semantic search...")
    semantic_query = "dragon with ice powers"
    results = memory_manager.search_similar(semantic_query, limit=2)
    print(f"Results for semantic query '{semantic_query}':")
    for i, result in enumerate(results):
        print(f"  {i+1}. {result.get('prompt', 'Unknown')} (id: {result.get('id', 'Unknown')})")
    
    # Test keyword search
    print("\nTesting keyword search...")
    keyword = "forest"
    results = memory_manager.keyword_search(keyword, limit=2)
    print(f"Results for keyword '{keyword}':")
    for i, result in enumerate(results):
        print(f"  {i+1}. {result.get('prompt', 'Unknown')} (id: {result.get('id', 'Unknown')})")
    
    # Test getting recent items
    print("\nTesting recent items...")
    results = memory_manager.get_recent(limit=3)
    print(f"Recent items:")
    for i, result in enumerate(results):
        print(f"  {i+1}. {result.get('prompt', 'Unknown')} (id: {result.get('id', 'Unknown')})")
    
    print("\nChromaDB test completed successfully!")

if __name__ == "__main__":
    # Create directories if they don't exist
    datastore_dir = os.path.join(os.path.dirname(__file__), "datastore")
    chroma_dir = os.path.join(datastore_dir, "chroma_db")
    os.makedirs(datastore_dir, exist_ok=True)
    os.makedirs(chroma_dir, exist_ok=True)
    
    # Run the test
    test_chromadb()