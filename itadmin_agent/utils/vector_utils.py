"""
Vector Database Utilities

This module provides utilities for working with vector databases,
including embedding generation and similarity search.
"""
import os
import logging
import json
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path

import numpy as np
import openai
import chromadb
from chromadb.config import Settings

from utils.logging_setup import get_agent_logger


class VectorDBClient:
    """Client for interacting with vector databases."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the vector database client.
        
        Args:
            config: Configuration dictionary
        """
        self.logger = get_agent_logger("vector_db")
        self.logger.info("Initializing Vector DB Client")
        
        self.config = config
        
        # Set up OpenAI API key
        openai.api_key = os.environ.get("OPENAI_API_KEY", "")
        if not openai.api_key:
            self.logger.warning("OpenAI API key not found in environment variables")
        
        # Initialize ChromaDB client
        self.persistent_path = Path(self.config.get('path', './data/vector_store'))
        os.makedirs(self.persistent_path, exist_ok=True)
        
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.persistent_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.embedding_model = self.config.get('embedding_model', 'text-embedding-ada-002')
        self.embedding_dimension = self.config.get('dimension', 1536)
        
        self.logger.info(f"Vector DB Client initialized with model {self.embedding_model}")
    
    def get_or_create_collection(self, collection_name: str) -> Any:
        """
        Get or create a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection object
        """
        try:
            # Try to get existing collection
            collection = self.chroma_client.get_collection(name=collection_name)
            self.logger.debug(f"Retrieved existing collection: {collection_name}")
            return collection
        except ValueError:
            # Collection doesn't exist, create it
            collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self.logger.info(f"Created new collection: {collection_name}")
            return collection
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for a text string.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            response = openai.Embedding.create(
                model=self.embedding_model,
                input=text
            )
            embedding = response['data'][0]['embedding']
            return embedding
        except Exception as e:
            self.logger.error(f"Error generating embedding: {str(e)}", exc_info=True)
            # Return a zero embedding as fallback
            return [0.0] * self.embedding_dimension
    
    def add_to_collection(self, collection_name: str, documents: List[str], 
                        metadata_list: List[Dict[str, Any]], ids: List[str]) -> bool:
        """
        Add documents to a collection.
        
        Args:
            collection_name: Name of the collection
            documents: List of document texts
            metadata_list: List of metadata dictionaries
            ids: List of document IDs
            
        Returns:
            True if successful, False otherwise
        """
        if not documents or len(documents) == 0:
            self.logger.warning("No documents provided to add_to_collection")
            return False
        
        if len(documents) != len(metadata_list) or len(documents) != len(ids):
            self.logger.error("Mismatch in lengths of documents, metadata, and IDs")
            return False
        
        try:
            collection = self.get_or_create_collection(collection_name)
            
            # Generate embeddings for all documents
            embeddings = []
            for doc in documents:
                embedding = self.generate_embedding(doc)
                embeddings.append(embedding)
            
            # Convert metadata to JSON strings to ensure compatibility
            serialized_metadata = []
            for meta in metadata_list:
                serialized_meta = {}
                for key, value in meta.items():
                    if isinstance(value, (dict, list)):
                        serialized_meta[key] = json.dumps(value)
                    else:
                        serialized_meta[key] = str(value)
                serialized_metadata.append(serialized_meta)
            
            # Add to collection
            collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=serialized_metadata,
                ids=ids
            )
            
            self.logger.info(f"Added {len(documents)} documents to collection {collection_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding to collection {collection_name}: {str(e)}", exc_info=True)
            return False
    
    def query_collection(self, collection_name: str, query_text: str, 
                       filter_criteria: Optional[Dict[str, Any]] = None, 
                       limit: int = 5) -> List[Dict[str, Any]]:
        """
        Query a collection for similar documents.
        
        Args:
            collection_name: Name of the collection
            query_text: Query text
            filter_criteria: Filter criteria for metadata
            limit: Maximum number of results
            
        Returns:
            List of results with documents, metadata, and distances
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            
            # Generate embedding for query
            query_embedding = self.generate_embedding(query_text)
            
            # Convert filter criteria to a format ChromaDB can use
            where_filter = None
            if filter_criteria:
                where_filter = {}
                for key, value in filter_criteria.items():
                    if isinstance(value, (list, dict)):
                        where_filter[key] = json.dumps(value)
                    else:
                        where_filter[key] = str(value)
            
            # Execute query
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_filter
            )
            
            # Process results
            processed_results = []
            for i in range(len(results['ids'][0])):
                # Parse serialized metadata
                metadata = results['metadatas'][0][i]
                deserialized_metadata = {}
                
                for key, value in metadata.items():
                    try:
                        # Try to parse as JSON
                        deserialized_metadata[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        # Not a JSON string, keep as is
                        deserialized_metadata[key] = value
                
                processed_results.append({
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': deserialized_metadata,
                    'distance': results['distances'][0][i]
                })
            
            self.logger.info(f"Query on collection {collection_name} returned {len(processed_results)} results")
            return processed_results
            
        except Exception as e:
            self.logger.error(f"Error querying collection {collection_name}: {str(e)}", exc_info=True)
            return []
    
    def delete_from_collection(self, collection_name: str, ids: List[str]) -> bool:
        """
        Delete documents from a collection.
        
        Args:
            collection_name: Name of the collection
            ids: List of document IDs to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            
            collection.delete(ids=ids)
            
            self.logger.info(f"Deleted {len(ids)} documents from collection {collection_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting from collection {collection_name}: {str(e)}", exc_info=True)
            return False
    
    def update_in_collection(self, collection_name: str, document: str,
                          metadata: Dict[str, Any], doc_id: str) -> bool:
        """
        Update a document in a collection.
        
        Args:
            collection_name: Name of the collection
            document: Document text
            metadata: Metadata dictionary
            doc_id: Document ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete the old entry
            self.delete_from_collection(collection_name, [doc_id])
            
            # Add the new entry
            success = self.add_to_collection(
                collection_name=collection_name,
                documents=[document],
                metadata_list=[metadata],
                ids=[doc_id]
            )
            
            if success:
                self.logger.info(f"Updated document {doc_id} in collection {collection_name}")
                return True
            else:
                self.logger.error(f"Failed to update document {doc_id} in collection {collection_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating in collection {collection_name}: {str(e)}", exc_info=True)
            return False
    
    def get_collection_count(self, collection_name: str) -> int:
        """
        Get the number of documents in a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Number of documents in the collection
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            count = collection.count()
            return count
            
        except Exception as e:
            self.logger.error(f"Error getting count for collection {collection_name}: {str(e)}", exc_info=True)
            return 0
    
    def list_collections(self) -> List[str]:
        """
        List all collections.
        
        Returns:
            List of collection names
        """
        try:
            collections = self.chroma_client.list_collections()
            return [c.name for c in collections]
            
        except Exception as e:
            self.logger.error(f"Error listing collections: {str(e)}", exc_info=True)
            return [] 