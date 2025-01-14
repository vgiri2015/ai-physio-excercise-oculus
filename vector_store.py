import faiss
import numpy as np
from typing import List, Dict, Optional
import pickle
import os

class VectorStore:
    def __init__(self, dimension: int = 1536):
        """Initialize the vector store with OpenAI's embedding dimension (1536 by default)."""
        self.dimension = dimension
        self.index = None
        self.document_map = {}  # Maps vector IDs to original documents
        
    def create_index(self, embeddings: np.ndarray, documents: List[Dict] = None):
        """Create a new FAISS index with the given embeddings."""
        if len(embeddings.shape) != 2 or embeddings.shape[1] != self.dimension:
            raise ValueError(f"Embeddings must be a 2D array with shape (n, {self.dimension})")
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Add vectors to the index
        self.index.add(embeddings.astype('float32'))
        
        # Store document mapping if provided
        if documents:
            for i, doc in enumerate(documents):
                self.document_map[i] = doc
                
    def search(self, query_vector: np.ndarray, k: int = 5) -> List[Dict]:
        """Search for k nearest neighbors of the query vector."""
        if self.index is None:
            raise ValueError("Index not initialized. Call create_index first.")
            
        # Reshape query vector if necessary
        if len(query_vector.shape) == 1:
            query_vector = query_vector.reshape(1, -1)
            
        # Perform the search
        distances, indices = self.index.search(query_vector.astype('float32'), k)
        
        # Return results with documents if available
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            result = {
                'distance': float(dist),
                'index': int(idx)
            }
            if idx in self.document_map:
                result['document'] = self.document_map[idx]
            results.append(result)
            
        return results
    
    def save(self, filepath: str):
        """Save the vector store to disk."""
        if self.index is None:
            raise ValueError("Nothing to save. Index not initialized.")
            
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, f"{filepath}.faiss")
        
        # Save document mapping
        with open(f"{filepath}.docs", 'wb') as f:
            pickle.dump(self.document_map, f)
            
    def load(self, filepath: str):
        """Load the vector store from disk."""
        # Load FAISS index
        self.index = faiss.read_index(f"{filepath}.faiss")
        
        # Load document mapping if it exists
        docs_path = f"{filepath}.docs"
        if os.path.exists(docs_path):
            with open(docs_path, 'rb') as f:
                self.document_map = pickle.load(f)
                
    def add_vectors(self, embeddings: np.ndarray, documents: List[Dict] = None):
        """Add new vectors to the existing index."""
        if self.index is None:
            self.create_index(embeddings, documents)
            return
            
        # Add vectors to the index
        self.index.add(embeddings.astype('float32'))
        
        # Update document mapping if provided
        if documents:
            current_size = len(self.document_map)
            for i, doc in enumerate(documents):
                self.document_map[current_size + i] = doc
                
    def get_document(self, index: int) -> Optional[Dict]:
        """Retrieve the document associated with a vector index."""
        return self.document_map.get(index)
        
    def __len__(self):
        """Return the number of vectors in the index."""
        return self.index.ntotal if self.index is not None else 0
