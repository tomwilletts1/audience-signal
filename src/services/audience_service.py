# src/services/audience_service.py
import json
from src.utils.logger import app_logger

class AudienceService:
    """
    Manages the creation, retrieval, and sampling of audiences.
    """
    def __init__(self, db_connection, persona_service):
        """
        Initializes the AudienceService.

        Args:
            db_connection: An active database connection/session.
            persona_service: An instance of the PersonaService.
        """
        self.db = db_connection
        self.persona_service = persona_service
        app_logger.info("AudienceService initialized.")

    def create_audience_from_filters(self, name: str, audience_type: str, criteria: dict, owner_id: str = None):
        """
        Creates a new audience in the database based on a set of filters.

        Args:
            name (str): The name for the new audience.
            audience_type (str): The type of audience ('geo', 'niche', 'custom').
            criteria (dict): A dictionary of filters (e.g., {'region': 'Manchester', 'age_min': 18}).
            owner_id (str, optional): The ID of the user/client who owns this audience.

        Returns:
            dict: A dictionary representing the newly created audience.
        """
        app_logger.info(f"Creating audience '{name}' with criteria: {criteria}")
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO audiences (name, type, criteria, owner_id) VALUES (?, ?, ?, ?)",
            (name, audience_type, json.dumps(criteria), owner_id)
        )
        self.db.commit()
        audience_id = cursor.lastrowid
        return {"id": audience_id, "name": name, "type": audience_type, "criteria": criteria}

    def get_audience_by_id(self, audience_id: str):
        """
        Retrieves a specific audience by its ID.
        """
        app_logger.info(f"Fetching audience with id: {audience_id}")
        cursor = self.db.cursor()
        cursor.execute("SELECT id, name, type, criteria, owner_id FROM audiences WHERE id = ?", (audience_id,))
        row = cursor.fetchone()
        if not row:
            return {"error": "Audience not found"}
        return {
            "id": row[0],
            "name": row[1],
            "type": row[2],
            "criteria": json.loads(row[3]) if row[3] else {},
            "owner_id": row[4]
        }

    def list_all_audiences(self):
        """
        Lists all available audiences.
        """
        app_logger.info("Listing all audiences.")
        cursor = self.db.cursor()
        cursor.execute("SELECT id, name, type, criteria, owner_id FROM audiences")
        rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "name": row[1],
                "type": row[2],
                "criteria": json.loads(row[3]) if row[3] else {},
                "owner_id": row[4]
            }
            for row in rows
        ]

    def sample_personas_from_audience(self, audience_id: str, count: int = 8):
        """
        Samples a number of personas that fit the audience criteria.

        Args:
            audience_id (str): The ID of the audience to sample from.
            count (int): The number of personas to sample.

        Returns:
            list: A list of persona detail dictionaries.
        """
        app_logger.info(f"Sampling {count} personas from audience {audience_id}.")
        # TODO: Use criteria to sample real personas. For now, return placeholders.
        return [f"Persona {i+1} for audience {audience_id}" for i in range(count)] 