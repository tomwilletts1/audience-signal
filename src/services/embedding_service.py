# src/services/embedding_service.py
import chromadb
from src.utils.logger import app_logger

class EmbeddingService:
    """
    Handles all communication with the vector database (ChromaDB).
    """
    def __init__(self, persistent_path: str = "chroma_db"):
        """
        Initializes the ChromaDB client.
        In a production environment, you might use a persistent client.
        For local dev, an in-memory instance is fine.
        """
        try:
            # For persistent storage, use:
            # self.client = chromadb.PersistentClient(path=persistent_path)
            # For now, using in-memory for simplicity
            self.client = chromadb.Client()
            self.collection = self.client.get_or_create_collection("persona_embeddings")
            app_logger.info("EmbeddingService initialized with ChromaDB collection 'persona_embeddings'.")
        except Exception as e:
            app_logger.error(f"Failed to initialize ChromaDB client: {e}", exc_info=True)
            raise

    def add_persona_embedding(self, persona_id: str, embedding_vector: list, metadata: dict = None):
        """
        Adds or updates a persona's embedding in ChromaDB.

        Args:
            persona_id (str): The unique ID of the persona.
            embedding_vector (list): The embedding vector.
            metadata (dict, optional): Additional metadata to store with the vector.
        """
        try:
            self.collection.add(
                embeddings=[embedding_vector],
                metadatas=[metadata or {}],
                ids=[persona_id]
            )
            app_logger.info(f"Added embedding for persona_id: {persona_id}")
        except Exception as e:
            app_logger.error(f"Failed to add embedding for persona_id {persona_id}: {e}", exc_info=True)

    def find_similar_personas(self, query_vector: list, n_results: int = 5, where_filter: dict = None):
        """
        Finds similar personas based on a query vector.

        Args:
            query_vector (list): The vector to search against.
            n_results (int): The number of similar results to return.
            where_filter (dict, optional): A filter to apply to the search.

        Returns:
            list: A list of similar persona IDs and their distances.
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=n_results,
                where=where_filter
            )
            app_logger.info(f"Found {len(results.get('ids', [[]])[0])} similar personas.")
            return results
        except Exception as e:
            app_logger.error(f"Failed to query ChromaDB for similar personas: {e}", exc_info=True)
            return None 