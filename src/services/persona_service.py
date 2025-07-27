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

    def generate_ephemeral_persona(self, region: str) -> dict:
        """
        Generates a persona's data without storing it in the database.
        This is ideal for on-the-fly sampling for focus groups.
        """
        app_logger.info(f"Generating ephemeral persona for {region}.")
        
        try:
            demographics = self.ons_data_service.sample_profile(region)
            
            # Handle case where ONS service returns an error
            if isinstance(demographics, dict) and "error" in demographics:
                demographics = self._generate_fallback_demographics(region)
            
            # Ensure we have a name
            if 'name' not in demographics or not demographics['name']:
                import random
                names = ['Alex', 'Sam', 'Jordan', 'Taylor', 'Casey', 'Morgan', 'Riley', 'Avery']
                demographics['name'] = random.choice(names)
            
            description = self._generate_persona_description(demographics)
            return {"description": description, "demographics": demographics}
            
        except Exception as e:
            app_logger.error(f"Error generating ephemeral persona for {region}: {e}")
            # Return a fallback persona to prevent simulation failure
            return {
                "description": "Alex, a 30-year-old professional living in the UK. They are a person with an income of £35000 per year.",
                "demographics": {"name": "Alex", "age": 30, "occupation": "professional", "gender": "person", "region": region, "income": 35000}
            }

    def _generate_fallback_demographics(self, region: str) -> dict:
        """Generate fallback demographics when ONS data is unavailable."""
        import random
        ages = [22, 25, 28, 32, 35, 38, 42, 45, 48, 52, 55, 58, 62, 65]
        occupations = ['teacher', 'engineer', 'manager', 'designer', 'consultant', 'analyst', 'developer', 'nurse', 'accountant', 'chef', 'artist', 'lawyer']
        genders = ['male', 'female']
        
        # Generate a unique name by combining first and last names
        first_names = ['Alex', 'Sam', 'Jordan', 'Taylor', 'Casey', 'Morgan', 'Riley', 'Avery', 'Jamie', 'Blake', 'Cameron', 'Dana', 'Ellis', 'Finley', 'Harper', 'Jesse', 'Kelly', 'Logan', 'Max', 'Noel', 'Parker', 'Quinn', 'River', 'Sage', 'Tatum', 'Val', 'Wren', 'Zion', 'Adrian', 'Bailey', 'Chloe', 'Dylan', 'Emma', 'Felix', 'Grace', 'Henry', 'Iris', 'Jack']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin']
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        
        return {
            'name': name,
            'age': random.choice(ages),
            'occupation': random.choice(occupations),
            'gender': random.choice(genders),
            'region': region,
            'income': random.randint(25000, 65000)
        }

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