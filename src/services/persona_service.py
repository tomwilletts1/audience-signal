# src/services/persona_service.py
from src.utils.logger import app_logger
import json

class PersonaService:
    """
    Handles the generation and management of individual AI personas.
    """
    def __init__(self, db_connection, embedding_service, ons_data_service):
        """
        Initializes the PersonaService.

        Args:
            db_connection: An active database connection/session.
            embedding_service: Service for vector database operations.
            ons_data_service: Service for ONS demographic data.
        """
        self.db = db_connection
        self.embedding_service = embedding_service
        self.ons_data_service = ons_data_service
        app_logger.info("PersonaService initialized.")

    def create_and_store_persona(self, audience_id: str, region: str, source: str = 'ons'):
        """
        Generates a persona, its embedding, and stores it in the database.

        Args:
            audience_id (str): The audience this persona belongs to.
            region (str): The geographical region for the persona.
            source (str): The source of the persona data ('ons', 'client').

        Returns:
            dict: The created persona's data.
        """
        app_logger.info(f"Creating persona for audience {audience_id} in {region}.")

        # 1. Get a demographic profile from the ONS data service
        demographics = self.ons_data_service.sample_profile(region)

        # 2. Generate a text description for this persona
        description = self._generate_persona_description(demographics)

        # 3. Generate an embedding for the description
        # This will be an actual call to an embedding model like OpenAI's
        embedding_vector = [0.1, 0.2, 0.3] # Placeholder

        # 4. Store the persona in the SQL database
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO personas (audience_id, demographics, embedding_id, description, source) VALUES (?, ?, ?, ?, ?)",
            (audience_id, json.dumps(demographics), None, description, source)
        )
        self.db.commit()
        persona_id = cursor.lastrowid

        # 5. Store the embedding in ChromaDB
        self.embedding_service.add_persona_embedding(str(persona_id), embedding_vector, metadata=demographics)
        
        return {"id": persona_id, "description": description, "demographics": demographics}

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

    def get_persona_response_to_stimulus(self, persona_id: str, stimulus: dict):
        """
        Generates a response from a specific persona to a given stimulus (message/image).
        This will use the RAG pattern by retrieving context.

        Args:
            persona_id (str): The ID of the persona responding.
            stimulus (dict): The stimulus material.

        Returns:
            str: The AI-generated response.
        """
        app_logger.info(f"Generating response from persona {persona_id}.")
        # TODO:
        # 1. Fetch persona details (demographics, description) from the database.
        # 2. Fetch relevant cultural context using the persona's embedding via EmbeddingService (RAG).
        # 3. Construct a detailed prompt for the LLM including persona, stimulus, and context.
        # 4. Call the LLM and return the response.
        return f"This is a simulated response from persona {persona_id}." 