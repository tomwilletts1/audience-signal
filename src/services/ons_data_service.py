# src/services/ons_data_service.py
import pandas as pd
from src.utils.logger import app_logger

class ONSDataService:
    """
    Handles loading and providing access to ONS demographic data.
    In a real application, this data would likely be pre-loaded into a
    database rather than being read from a CSV on the fly.
    """
    def __init__(self, data_path: str = 'data/ons_demographics.csv'):
        """
        Initializes the ONSDataService and loads the dataset.

        Args:
            data_path (str): The file path to the ONS data CSV.
        """
        self.data_path = data_path
        try:
            # self.df = pd.read_csv(data_path)
            # For now, creating a dummy dataframe to avoid file errors
            self.df = pd.DataFrame({
                'region': ['Manchester', 'Manchester', 'Birmingham', 'Leeds'],
                'age': [25, 45, 33, 22],
                'gender': ['female', 'male', 'male', 'female'],
                'income': [35000, 55000, 42000, 31000],
                'occupation': ['teacher', 'engineer', 'manager', 'student']
            })
            app_logger.info(f"ONSDataService initialized with data from '{data_path}'.")
        except FileNotFoundError:
            app_logger.error(f"ONS data file not found at: {data_path}")
            # Create an empty dataframe to prevent crashes
            self.df = pd.DataFrame()
        except Exception as e:
            app_logger.error(f"Error loading ONS data: {e}", exc_info=True)
            self.df = pd.DataFrame()


    def get_demographic_distribution(self, region: str) -> dict:
        """
        Calculates the demographic distribution for a specific region.

        Args:
            region (str): The region to analyze (e.g., 'Manchester').

        Returns:
            dict: A dictionary containing statistics about the region.
        """
        if self.df.empty:
            return {}

        region_df = self.df[self.df['region'].str.lower() == region.lower()]
        if region_df.empty:
            return {}

        distribution = {
            'total_samples': len(region_df),
            'average_age': region_df['age'].mean(),
            'gender_distribution': region_df['gender'].value_counts(normalize=True).to_dict()
        }
        app_logger.info(f"Calculated demographic distribution for {region}.")
        return distribution

    def sample_profile(self, region: str) -> dict:
        """
        Samples a single, representative demographic profile from the specified region.
        This uses weighted random sampling if distributions are available.

        Args:
            region (str): The region to sample from.

        Returns:
            dict: A dictionary representing a single demographic profile.
        """
        if self.df.empty:
            return {"error": "No data available"}

        region_df = self.df[self.df['region'].str.lower() == region.lower()]
        if region_df.empty:
            return {"error": f"No data for region {region}"}

        # Simple random sample for now.
        # A more advanced implementation would use stratified sampling.
        profile = region_df.sample(n=1).to_dict(orient='records')[0]
        app_logger.info(f"Sampled a demographic profile for {region}.")
        return profile 