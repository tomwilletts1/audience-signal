# src/services/data_service.py - Consolidated Data Service
import sqlite3
import pandas as pd
from typing import Dict, List, Optional
from src.utils.logger import app_logger

class DataService:
    """Consolidated service for all data operations: ONS, City, and Client data."""
    
    def __init__(self, db_path: str = 'audience_engine.db', ons_data_path: str = 'data/ons_demographics.csv'):
        self.db_path = db_path
        self.ons_data_path = ons_data_path
        self.ons_df = self._load_ons_data()
        app_logger.info("DataService initialized with ONS, City, and Client data capabilities.")

    # ==================== ONS DATA OPERATIONS ====================
    def _load_ons_data(self):
        """Load ONS demographic data."""
        try:
            # For now, using dummy data to avoid file errors
            df = pd.DataFrame({
                'region': ['Manchester', 'Manchester', 'Birmingham', 'Leeds', 'Liverpool', 'Liverpool', 
                          'London', 'London', 'Newcastle', 'Cardiff', 'Oxford', 'Norwich'],
                'age': [25, 45, 33, 22, 35, 28, 29, 41, 31, 27, 24, 38],
                'gender': ['female', 'male', 'male', 'female', 'male', 'female', 'female', 'male', 'male', 'female', 'male', 'female'],
                'income': [35000, 55000, 42000, 31000, 38000, 33000, 45000, 65000, 39000, 36000, 28000, 42000],
                'occupation': ['teacher', 'engineer', 'manager', 'student', 'healthcare', 'artist', 'consultant', 'banker', 'nurse', 'designer', 'student', 'teacher']
            })
            app_logger.info(f"ONS data loaded successfully with {len(df)} records.")
            return df
        except Exception as e:
            app_logger.error(f"Error loading ONS data: {e}", exc_info=True)
            return pd.DataFrame()

    def sample_ons_profile(self, region: str):
        """Sample a demographic profile from ONS data."""
        if self.ons_df.empty:
            app_logger.warning("ONS data is empty, returning default profile.")
            return {
                'name': 'John Doe',
                'age': 30,
                'gender': 'male',
                'income': 35000,
                'occupation': 'unknown',
                'region': region
            }

        # Filter by region if available
        region_data = self.ons_df[self.ons_df['region'].str.contains(region, case=False, na=False)]
        
        if region_data.empty:
            app_logger.warning(f"No data found for region '{region}', using random sample.")
            region_data = self.ons_df

        # Sample a random row
        if len(region_data) > 0:
            sample = region_data.sample(n=1).iloc[0]
            profile = {
                'name': f"Person {sample.name}",
                'age': sample['age'],
                'gender': sample['gender'],
                'income': sample['income'],
                'occupation': sample['occupation'],
                'region': region
            }
            app_logger.debug(f"Sampled ONS profile for {region}: {profile}")
            return profile
        else:
            app_logger.error("No data available for sampling.")
            return {
                'name': 'Default Person',
                'age': 30,
                'gender': 'unknown',
                'income': 35000,
                'occupation': 'unknown',
                'region': region
            }

    def get_ons_summary_stats(self, region: str = None):
        """Get ONS summary statistics."""
        if self.ons_df.empty:
            return {}

        data = self.ons_df
        if region:
            data = self.ons_df[self.ons_df['region'].str.contains(region, case=False, na=False)]

        return {
            'count': len(data),
            'avg_age': data['age'].mean() if len(data) > 0 else 0,
            'avg_income': data['income'].mean() if len(data) > 0 else 0,
            'region': region or 'All'
        }

    # ==================== CITY DATA OPERATIONS ====================
    def get_city_profile(self, city_name: str) -> Optional[Dict]:
        """Get complete city profile with economic and cultural data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    c.city_name,
                    c.population_estimate,
                    c.population_year,
                    e.employment_rate,
                    e.median_weekly_pay,
                    e.gdhi_per_person,
                    e.unemployment_rate,
                    cu.arts_engagement_percent,
                    cu.museum_visits_percent,
                    cu.heritage_visits_percent
                FROM cities c
                LEFT JOIN city_economic_indicators e ON c.id = e.city_id
                LEFT JOIN city_cultural_engagement cu ON c.id = cu.city_id
                WHERE c.city_name = ?
            ''', (city_name,))
            
            result = cursor.fetchone()
            
            if result:
                return {
                    'city_name': result[0],
                    'population_estimate': result[1],
                    'population_year': result[2],
                    'employment_rate': result[3],
                    'median_weekly_pay': result[4],
                    'gdhi_per_person': result[5],
                    'unemployment_rate': result[6],
                    'arts_engagement_percent': result[7],
                    'museum_visits_percent': result[8],
                    'heritage_visits_percent': result[9]
                }
            return None
            
        except Exception as e:
            app_logger.error(f"Error getting city profile for {city_name}: {e}", exc_info=True)
            return None
        finally:
            conn.close()

    def create_city_audience(self, city_name: str) -> Dict:
        """Create audience personas based on real city data."""
        city_profile = self.get_city_profile(city_name)
        
        if not city_profile:
            raise ValueError(f"No data found for city: {city_name}")
        
        # Create personas based on real data
        personas = [
            f"Sarah Mitchell, 32, Digital Marketing Manager, {city_name} city centre, "
            f"Arts engagement: {city_profile['arts_engagement_percent']}%, "
            f"Median weekly pay: £{city_profile['median_weekly_pay']}, "
            f"Employment rate: {city_profile['employment_rate']}%",
            
            f"James Thompson, 28, Software Developer, {city_name} tech district, "
            f"Museum visits: {city_profile['museum_visits_percent']}%, "
            f"Cultural engagement: High, "
            f"GDHI per person: £{city_profile['gdhi_per_person']:,}",
            
            f"Emma Wilson, 35, Healthcare Worker, {city_name} suburbs, "
            f"Heritage visits: {city_profile['heritage_visits_percent']}%, "
            f"Stable employment, "
            f"Community-focused lifestyle"
        ]
        
        return {
            'name': city_name,
            'description': f"Residents of {city_name} (Population: {city_profile['population_estimate']:,}, {city_profile['population_year']})",
            'personas': personas,
            'economic_data': city_profile
        }

    def get_all_cities(self) -> List[Dict]:
        """Get list of all available cities."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT city_name, population_estimate, population_year FROM cities ORDER BY population_estimate DESC')
            results = cursor.fetchall()
            
            cities = []
            for result in results:
                cities.append({
                    'name': result[0],
                    'population': result[1],
                    'year': result[2]
                })
            
            return cities
        except Exception as e:
            app_logger.error(f"Error getting cities list: {e}", exc_info=True)
            return []
        finally:
            conn.close()

    # ==================== CLIENT DATA OPERATIONS ====================
    def process_client_file(self, file_path: str, owner_id: str, audience_name: str):
        """Process client-uploaded data file."""
        app_logger.info(f"Processing client file '{file_path}' for owner '{owner_id}'.")
        
        try:
            # Read the file based on extension
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format. Please use CSV or Excel files.")
            
            app_logger.info(f"File loaded successfully: {len(df)} rows, {len(df.columns)} columns.")
            
            # Basic validation
            if df.empty:
                raise ValueError("The uploaded file is empty.")
            
            # Process and create audience
            result = self._create_client_audience(df, owner_id, audience_name)
            
            app_logger.info(f"Client audience '{audience_name}' created successfully.")
            return result
            
        except Exception as e:
            app_logger.error(f"Error processing client file: {e}", exc_info=True)
            raise

    def _create_client_audience(self, df: pd.DataFrame, owner_id: str, audience_name: str):
        """Create audience from client data."""
        # Basic audience creation logic
        sample_size = min(len(df), 10)  # Sample up to 10 records
        sample_data = df.head(sample_size)
        
        # Generate personas from the data
        personas = []
        for _, row in sample_data.iterrows():
            persona_parts = []
            for col, val in row.items():
                if pd.notna(val):
                    persona_parts.append(f"{col}: {val}")
            
            persona_description = ", ".join(persona_parts[:5])  # Limit to first 5 fields
            personas.append(persona_description)
        
        audience_data = {
            'name': audience_name,
            'owner_id': owner_id,
            'type': 'client_uploaded',
            'personas': personas,
            'record_count': len(df),
            'columns': list(df.columns)
        }
        
        # Store in database (simplified)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO audiences (name, type, criteria, owner_id, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            ''', (audience_name, 'client_uploaded', f"Uploaded data with {len(df)} records", owner_id))
            
            audience_id = cursor.lastrowid
            
            # Store personas
            for persona_desc in personas:
                cursor.execute('''
                    INSERT INTO personas (audience_id, description, source, created_at)
                    VALUES (?, ?, ?, datetime('now'))
                ''', (audience_id, persona_desc, 'client_upload'))
            
            conn.commit()
            app_logger.info(f"Stored audience '{audience_name}' with {len(personas)} personas.")
            
        except Exception as e:
            conn.rollback()
            app_logger.error(f"Error storing client audience: {e}", exc_info=True)
            raise
        finally:
            conn.close()
        
        return audience_data 