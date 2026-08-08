import logging
from typing import Optional
from .chromadb_store import FailureMemory

logger = logging.getLogger(__name__)

class SimilaritySearcher:
    def __init__(self, failure_memory: FailureMemory):
        self.memory = failure_memory
        self.collection = failure_memory.collection

    def search_similar(self, sanitized_log: str, threshold: float = 0.80) -> Optional[dict]:
        """Search for similar past failures in ChromaDB."""
        try:
            # Query top 3 matches
            results = self.collection.query(
                query_texts=[sanitized_log],
                n_results=3
            )
            
            if not results['ids'] or not results['ids'][0]:
                logger.info("No similar failures found in memory.")
                return None
                
            # Process best match
            best_id = results['ids'][0][0]
            best_distance = results['distances'][0][0]
            best_metadata = results['metadatas'][0][0]
            
            similarity_score = max(0.0, 1.0 - best_distance)
            
            logger.info(f"Top match '{best_id}' found with distance {best_distance:.4f} (score: {similarity_score:.4f})")
            
            if similarity_score >= threshold:
                return {
                    'matched_id': best_id,
                    'similarity_score': similarity_score,
                    'previous_fix': best_metadata.get('suggested_fix', 'No fix recorded'),
                    'confidence': 'HIGH' if similarity_score > 0.9 else 'MEDIUM',
                    'matched_summary': best_metadata.get('summary', 'Unknown')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error during similarity search: {e}")
            return None
