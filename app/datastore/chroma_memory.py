import logging
import os
import json
import time
from typing import Dict, List, Optional, Any, Tuple
import chromadb
from chromadb.utils import embedding_functions

class ChromaMemoryManager:
    """
    Memory management using ChromaDB for vector similarity search
    """
    def __init__(self):
        # Set up logging
        logging.basicConfig(level=logging.INFO, 
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Create data directory if it doesn't exist
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datastore", "chroma_db")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=self.data_dir)
        
        # Create embedding function (using OpenAI's text-embedding for best results)
        # In a production app, you would use an environment variable for the API key
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # Create or get the collection for our prompts and images
        try:
            self.collection = self.client.get_collection(
                name="dragon_memory", 
                embedding_function=self.embedding_function
            )
            logging.info("Connected to existing ChromaDB collection 'dragon_memory'")
        except:
            # Collection doesn't exist, create it
            self.collection = self.client.create_collection(
                name="dragon_memory", 
                embedding_function=self.embedding_function
            )
            logging.info("Created new ChromaDB collection 'dragon_memory'")
        
    def store(self, prompt: str, expanded_prompt: str, image_path: str, model_path: str, tags: List[str] = None):
        """
        Store a creation in the vector database with its embedding for similarity search
        
        Args:
            prompt (str): Original user prompt
            expanded_prompt (str): LLM-expanded prompt
            image_path (str): Path to the generated image
            model_path (str): Path to the generated 3D model
            tags (List[str], optional): Tags for better search/retrieval
        """
        # Create unique ID based on timestamp
        memory_id = str(int(time.time()))
        
        # Combine prompt and tags for better embedding context
        combined_text = f"{prompt} {expanded_prompt} {' '.join(tags or [])}"
        
        # Create metadata object
        metadata = {
            "timestamp": time.time(),
            "prompt": prompt,
            "expanded_prompt": expanded_prompt,
            "image_path": image_path,
            "model_path": model_path,
            "tags": json.dumps(tags or [])
        }
        
        # Add to collection
        try:
            self.collection.add(
                ids=[memory_id],
                documents=[combined_text],
                metadatas=[metadata]
            )
            logging.info(f"Creation stored in ChromaDB with ID: {memory_id}")
        except Exception as e:
            logging.error(f"Error storing in ChromaDB: {e}")
    
    def search_similar(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search for similar memories based on semantic similarity
        
        Args:
            query (str): Search query
            limit (int): Maximum number of results to return
            
        Returns:
            List[Dict]: Similar memories
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            # Process results
            memories = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    memory_id = results["ids"][0][i]
                    metadata = results["metadatas"][0][i]
                    
                    # Parse tags from JSON string
                    if "tags" in metadata:
                        metadata["tags"] = json.loads(metadata["tags"])
                    
                    memories.append({
                        "id": memory_id,
                        **metadata
                    })
            
            return memories
        except Exception as e:
            logging.error(f"Error searching ChromaDB: {e}")
            return []
    
    def keyword_search(self, keyword: str, limit: int = 5) -> List[Dict]:
        """
        Search for memories based on keyword matching
        
        Args:
            keyword (str): Keyword to search for
            limit (int): Maximum number of results to return
            
        Returns:
            List[Dict]: Matching memories
        """
        try:
            # Use where filter on metadata
            results = self.collection.query(
                query_texts=[""],  # Empty query to make it work with where filter
                where_document={"$contains": keyword},
                n_results=limit
            )
            
            # Process results
            memories = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    memory_id = results["ids"][0][i]
                    metadata = results["metadatas"][0][i]
                    
                    # Parse tags from JSON string
                    if "tags" in metadata:
                        metadata["tags"] = json.loads(metadata["tags"])
                    
                    memories.append({
                        "id": memory_id,
                        **metadata
                    })
            
            return memories
        except Exception as e:
            logging.error(f"Error keyword searching ChromaDB: {e}")
            return []
    
    def get_recent(self, limit: int = 5) -> List[Dict]:
        """
        Get most recent creations
        
        Args:
            limit (int): Maximum number of results to return
            
        Returns:
            List[Dict]: Recent memories
        """
        try:
            # Get all items
            results = self.collection.get(limit=limit)
            
            # Sort by timestamp (descending)
            memories = []
            if results["ids"] and len(results["ids"]) > 0:
                memories_with_ts = []
                for i in range(len(results["ids"])):
                    memory_id = results["ids"][i]
                    metadata = results["metadatas"][i]
                    
                    # Parse tags from JSON string
                    if "tags" in metadata:
                        metadata["tags"] = json.loads(metadata["tags"])
                    
                    memory = {
                        "id": memory_id,
                        **metadata
                    }
                    memories_with_ts.append(memory)
                
                # Sort by timestamp (descending)
                memories = sorted(memories_with_ts, key=lambda x: x.get("timestamp", 0), reverse=True)
                
                # Limit results
                memories = memories[:limit]
            
            return memories
        except Exception as e:
            logging.error(f"Error getting recent items from ChromaDB: {e}")
            return []
    
    def close(self):
        """Close ChromaDB connection"""
        try:
            # No explicit close method for ChromaDB client, but we'll keep this for consistency
            pass
        except:
            pass