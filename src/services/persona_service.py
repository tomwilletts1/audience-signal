# src/services/persona_service.py
from src.utils.logger import app_logger
import json

class PersonaService:
    """
    Handles the generation and management of individual AI personas.
    """
    def __init__(self, db_connection, embedding_service, data_service):
        """
        Initializes the PersonaService.

        Args:
            db_connection: An active database connection/session.
            embedding_service: Service for vector database operations.
            data_service: Service for demographic and city data operations.
        """
        self.db = db_connection
        self.embedding_service = embedding_service
        self.data_service = data_service
        app_logger.info("PersonaService initialized.")

    def create_persona(self, persona_id: str, region: str = "UK") -> dict:
        """
        Creates a new persona with realistic demographic characteristics.

        Args:
            persona_id (str): Unique identifier for the persona.
            region (str): Geographic region to sample demographics from.

        Returns:
            dict: Generated persona with demographics and description.
        """
        # Sample demographics from data service
        demographics = self.data_service.sample_ons_profile(region)
        
        # Generate persona description
        description = self._generate_persona_description(demographics)
        
        # Generate embeddings for the persona (placeholder for future RAG)
        embedding = self._generate_persona_embedding(description)
        
        persona = {
            'id': persona_id,
            'demographics': demographics,
            'description': description,
            'embedding': embedding,
            'region': region
        }
        
        app_logger.debug(f"Created persona {persona_id} for region {region}")
        return persona

    def _generate_persona_description(self, demographics: dict) -> str:
        """
        Creates a rich text description of a persona from demographic data.
        This can be a simple f-string or a call to an LLM for a more narrative style.
        """
        desc = (
            f"{demographics.get('name', 'Alex')}, a {demographics.get('age', 30)}-year-old "
            f"{demographics.get('occupation', 'professional')} living in {demographics.get('region', 'the UK')}. "
            f"They are a {demographics.get('gender', 'person')} with an income of "
            f"£{demographics.get('income', 35000)} per year."
        )
        return desc

    def _generate_persona_embedding(self, description: str):
        """
        Generates vector embeddings for the persona description.
        This enables similarity searches and persona clustering.
        """
        try:
            # Use embedding service to generate vectors
            embedding = self.embedding_service.generate_embedding(description)
            return embedding
        except Exception as e:
            app_logger.warning(f"Failed to generate embedding for persona: {e}")
            return None

    def get_persona_response_to_stimulus(self, persona_data: dict, stimulus: str) -> str:
        """
        Generates a persona's response to a marketing stimulus.
        This is a placeholder that would use an LLM service in practice.
        """
        # TODO: Implement actual LLM call through AI service
        app_logger.debug(f"Generating response for persona {persona_data.get('id', 'unknown')}")
        
        # Placeholder response
        response = (
            f"As {persona_data['description']}, I think this stimulus is interesting. "
            f"It relates to my background because..."
        )
        return response

    def store_persona(self, persona: dict):
        """
        Stores a persona in the database.
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO personas 
                (id, demographics, description, embedding, region, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (
                persona['id'],
                json.dumps(persona['demographics']),
                persona['description'],
                json.dumps(persona.get('embedding', [])),
                persona['region']
            ))
            self.db.commit()
            app_logger.info(f"Stored persona {persona['id']} in database")
        except Exception as e:
            app_logger.error(f"Error storing persona {persona['id']}: {e}", exc_info=True)
            raise

    def retrieve_persona(self, persona_id: str) -> dict:
        """
        Retrieves a persona from the database.
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT id, demographics, description, embedding, region, created_at
                FROM personas WHERE id = ?
            """, (persona_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'demographics': json.loads(result[1]),
                    'description': result[2],
                    'embedding': json.loads(result[3]),
                    'region': result[4],
                    'created_at': result[5]
                }
            return None
        except Exception as e:
            app_logger.error(f"Error retrieving persona {persona_id}: {e}", exc_info=True)
            raise

    def list_personas_by_region(self, region: str) -> list:
        """
        Lists all personas from a specific region.
        """
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT id, demographics, description, region, created_at
                FROM personas WHERE region = ?
                ORDER BY created_at DESC
            """, (region,))
            
            results = cursor.fetchall()
            personas = []
            for result in results:
                personas.append({
                    'id': result[0],
                    'demographics': json.loads(result[1]),
                    'description': result[2],
                    'region': result[3],
                    'created_at': result[4]
                })
            
            app_logger.debug(f"Retrieved {len(personas)} personas for region {region}")
            return personas
        except Exception as e:
            app_logger.error(f"Error listing personas for region {region}: {e}", exc_info=True)
            raise 