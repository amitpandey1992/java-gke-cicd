import chromadb
from typing import Optional

class FailureMemory:
    def __init__(self, persist_directory: str):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name='failure_memory')

    def store_failure(self, analysis_id: str, sanitized_log: str, analysis_result: dict) -> None:
        """Store a analyzed failure in ChromaDB."""
        # Convert any non-string, non-numeric values in metadata to string for chromadb compatibility
        metadata = {}
        for k, v in analysis_result.items():
            if isinstance(v, (str, int, float, bool)):
                metadata[k] = v
            else:
                metadata[k] = str(v)
                
        self.collection.add(
            documents=[sanitized_log],
            metadatas=[metadata],
            ids=[analysis_id]
        )

    def get_failure(self, analysis_id: str) -> Optional[dict]:
        """Retrieve a specific failure by ID."""
        results = self.collection.get(ids=[analysis_id])
        if not results or not results['ids']:
            return None
            
        return {
            'id': results['ids'][0],
            'document': results['documents'][0] if results['documents'] else None,
            'metadata': results['metadatas'][0] if results['metadatas'] else None
        }
