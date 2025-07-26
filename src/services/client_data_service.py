# src/services/client_data_service.py
import pandas as pd
from src.utils.logger import app_logger

class ClientDataService:
    """
    Handles the ingestion, processing, and management of client-provided data.
    """
    def __init__(self, db_connection, audience_service):
        """
        Initializes the ClientDataService.

        Args:
            db_connection: An active database connection/session.
            audience_service: Service for managing audiences.
        """
        self.db = db_connection
        self.audience_service = audience_service
        app_logger.info("ClientDataService initialized.")

    def process_uploaded_file(self, file_path: str, owner_id: str, client_audience_name: str):
        """
        Processes an uploaded CSV or Excel file to create a custom audience.

        Args:
            file_path (str): The path to the uploaded data file.
            owner_id (str): The ID of the client/user who owns this data.
            client_audience_name (str): The name for the new audience to be created.

        Returns:
            dict: A summary of the processing results.
        """
        app_logger.info(f"Processing uploaded file '{file_path}' for owner '{owner_id}'.")
        try:
            # Simple logic for reading a CSV. Add logic for other formats if needed.
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                raise ValueError("Unsupported file format. Please use CSV.")

            # Create a new audience for this client data
            criteria = {"source_file": file_path, "record_count": len(df)}
            audience = self.audience_service.create_audience_from_filters(
                name=client_audience_name,
                audience_type='client',
                criteria=criteria,
                owner_id=owner_id
            )
            
            # TODO: For each row, create a persona linked to this audience

            return {
                "status": "success",
                "message": f"Successfully processed {len(df)} records.",
                "audience_id": audience.get("id"),
                "audience_name": client_audience_name
            }

        except Exception as e:
            app_logger.error(f"Failed to process uploaded file {file_path}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    def map_columns(self, data_id: str, column_mapping: dict):
        """
        Maps columns from a client's uploaded file to the standard persona schema.
        This would be used in a more advanced UI flow.

        Args:
            data_id (str): The ID of the uploaded data batch.
            column_mapping (dict): A mapping like {'client_age_col': 'age', 'client_loc_col': 'region'}.
        """
        app_logger.info(f"Applying column mapping for data_id {data_id}: {column_mapping}")
        # TODO: Implement logic to update stored data with the correct schema.
        return {"status": "success", "message": "Column mapping applied."} 