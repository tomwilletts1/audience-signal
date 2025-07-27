# ingest_multiple_cities.py
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List
from src.utils.logger import app_logger

class CityDataIngester:
    def __init__(self, db_path: str = 'audience_engine.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
    
    def ingest_city_data(self, city_data: Dict[str, Any]):
        """Ingest complete city data including economic and cultural indicators"""
        
        try:
            # 1. Insert city basic info
            city_id = self._insert_city(city_data)
            
            # 2. Insert economic indicators
            self._insert_economic_indicators(city_id, city_data['economic_indicators'])
            
            # 3. Insert cultural engagement
            self._insert_cultural_engagement(city_id, city_data['cultural_engagement'])
            
            # 4. Insert confidence intervals
            self._insert_confidence_intervals(city_id, city_data)
            
            self.conn.commit()
            app_logger.info(f"Successfully ingested data for {city_data['city']}")
            return city_id
            
        except Exception as e:
            self.conn.rollback()
            app_logger.error(f"Failed to ingest {city_data['city']}: {e}", exc_info=True)
            raise
    
    def ingest_multiple_cities(self, cities_data: List[Dict[str, Any]]):
        """Ingest multiple cities in batch"""
        
        successful = 0
        failed = 0
        
        for city_data in cities_data:
            try:
                self.ingest_city_data(city_data)
                successful += 1
                print(f"✓ {city_data['city']} ingested successfully")
            except Exception as e:
                failed += 1
                print(f"✗ Failed to ingest {city_data['city']}: {e}")
        
        print(f"\n📊 Batch ingestion complete: {successful} successful, {failed} failed")
        return successful, failed
    
    def _insert_city(self, city_data: Dict[str, Any]) -> int:
        """Insert basic city information"""
        
        self.cursor.execute('''
            INSERT OR REPLACE INTO cities 
            (city_name, country, population_estimate, population_year)
            VALUES (?, ?, ?, ?)
        ''', (
            city_data['city'],
            city_data['country'],
            city_data['population']['estimate'],
            city_data['population']['year']
        ))
        
        return self.cursor.lastrowid
    
    def _insert_economic_indicators(self, city_id: int, economic_data: Dict[str, Any]):
        """Insert economic indicators"""
        
        self.cursor.execute('''
            INSERT OR REPLACE INTO city_economic_indicators 
            (city_id, data_year, economic_inactivity_rate, employment_rate, 
             unemployment_rate, claimant_count_rate, gdhi_per_person, 
             median_weekly_pay, gva_per_hour)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            city_id,
            economic_data['data_year']['inactivity_rate'],
            economic_data['economic_inactivity_rate']['value_percent'],
            economic_data['employment_rate']['value_percent'],
            economic_data['modelled_unemployment_rate']['value_percent'],
            economic_data['claimant_count_rate']['value_percent'],
            economic_data['gross_disposable_household_income_per_person']['value_gbp'],
            economic_data['gross_median_weekly_pay']['value_gbp'],
            economic_data['gva_per_hour_worked']['value_gbp']
        ))
    
    def _insert_cultural_engagement(self, city_id: int, cultural_data: Dict[str, Any]):
        """Insert cultural engagement data"""
        
        self.cursor.execute('''
            INSERT OR REPLACE INTO city_cultural_engagement 
            (city_id, data_year, arts_engagement_percent, heritage_visits_percent,
             museum_visits_percent, library_visits_percent)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            city_id,
            cultural_data['data_year'],
            cultural_data['arts_engagement']['value_percent'],
            cultural_data['heritage_site_visits']['value_percent'],
            cultural_data['museum_gallery_visits']['value_percent'],
            cultural_data['public_library_visits']['value_percent']
        ))
    
    def _insert_confidence_intervals(self, city_id: int, city_data: Dict[str, Any]):
        """Insert confidence intervals for detailed analysis"""
        
        # Economic confidence intervals
        economic_data = city_data['economic_indicators']
        cultural_data = city_data['cultural_engagement']
        
        intervals = [
            ('economic_inactivity_rate', economic_data['economic_inactivity_rate']),
            ('employment_rate', economic_data['employment_rate']),
            ('unemployment_rate', economic_data['modelled_unemployment_rate']),
            ('arts_engagement', cultural_data['arts_engagement']),
            ('heritage_visits', cultural_data['heritage_site_visits']),
            ('museum_visits', cultural_data['museum_gallery_visits']),
            ('library_visits', cultural_data['public_library_visits'])
        ]
        
        for metric_name, data in intervals:
            if 'confidence_interval' in data:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO confidence_intervals 
                    (city_id, metric_name, lower_bound, upper_bound)
                    VALUES (?, ?, ?, ?)
                ''', (
                    city_id,
                    metric_name,
                    data['confidence_interval']['lower'],
                    data['confidence_interval']['upper']
                ))
    
    def close(self):
        """Close database connection"""
        self.conn.close()

def get_sample_cities_data():
    """Sample data for multiple UK cities - Birmingham and Liverpool"""
    
    # Birmingham and Liverpool comprehensive city data
    return [
        {
            "city": "Birmingham",
            "country": "England",
            "population": {
                "source": "ONS mid‑year estimate 2022",
                "year": 2022,
                "estimate": 1157603,
                "growth_from_2021": 14318,
                "notes": "The mid‑2022 population of Birmingham was 1,157,603 with growth of 14,318 since 2021."
            },
            "cultural_engagement": {
                "data_year": "2023-2024",
                "arts_engagement": {
                    "description": "Percentage of adults who engaged with the arts physically in the last 12 months.",
                    "value_percent": 85,
                    "confidence_interval": { "lower": 83, "upper": 87 },
                    "source_table": "Table 78 (Engaged with the arts)"
                },
                "heritage_site_visits": {
                    "description": "Percentage of adults who visited a heritage site in the last 12 months.",
                    "value_percent": 55,
                    "confidence_interval": { "lower": 51, "upper": 59 },
                    "source_table": "Table 79 (Visited a heritage site)"
                },
                "museum_gallery_visits": {
                    "description": "Percentage of adults who visited a museum or gallery in person in the last 12 months.",
                    "value_percent": 31,
                    "confidence_interval": { "lower": 28, "upper": 34 },
                    "source_table": "Table 80 (Visited a museum or gallery)"
                },
                "public_library_visits": {
                    "description": "Percentage of adults who visited a public or mobile library in person in the last 12 months.",
                    "value_percent": 27,
                    "confidence_interval": { "lower": 24, "upper": 29 },
                    "source_table": "Table 81 (Visited a public library)"
                }
            },
            "economic_indicators": {
                "data_year": {
                    "inactivity_rate": 2023,
                    "employment_rate": 2023,
                    "unemployment_rate": 2023,
                    "claimant_count": 2024,
                    "gdhi_per_person": 2022,
                    "median_weekly_pay": "April 2024",
                    "gva_per_hour": 2023
                },
                "economic_inactivity_rate": {
                    "description": "Percentage of people aged 16–64 not in work and not seeking work.",
                    "value_percent": 28.3,
                    "confidence_interval": { "lower": 25.0, "upper": 31.6 },
                    "source_table": "Table 1 (Economic inactivity rate)"
                },
                "employment_rate": {
                    "description": "Percentage of people aged 16–64 in paid work.",
                    "value_percent": 65.9,
                    "confidence_interval": { "lower": 62.4, "upper": 69.4 },
                    "source_table": "Table 3 (Employment rate)"
                },
                "modelled_unemployment_rate": {
                    "description": "Percentage of economically active residents who are unemployed and looking for work.",
                    "value_percent": 7.2,
                    "confidence_interval": { "lower": 5.5, "upper": 8.9 },
                    "source_table": "Table 5 (Modelled unemployment rate)"
                },
                "claimant_count_rate": {
                    "description": "Proportion of working‑age residents receiving unemployment‑related benefits.",
                    "value_percent": 9.9,
                    "source_table": "Table 6 (Claimant Count)"
                },
                "gross_disposable_household_income_per_person": {
                    "description": "Amount households can spend or save after taxes and benefits.",
                    "value_gbp": 16950,
                    "units": "£ per person",
                    "source_table": "Table 7 (GDHI per person)"
                },
                "gross_median_weekly_pay": {
                    "description": "Median weekly pay for full‑time employees.",
                    "value_gbp": 565.4,
                    "confidence_interval": { "lower": 542.128, "upper": 588.672 },
                    "units": "£ per week",
                    "source_table": "Table 8 (Gross median weekly pay)"
                },
                "gva_per_hour_worked": {
                    "description": "Gross value added per hour worked—a labour productivity measure.",
                    "value_gbp": 35.1,
                    "units": "£ per hour",
                    "source_table": "Table 10 (GVA per hour)"
                }
            }
        },
        {
            "city": "Liverpool",
            "country": "England",
            "population": {
                "source": "Liverpool City Council mid‑2022 estimate",
                "year": 2022,
                "estimate": 495849,
                "growth_over_10_years_percent": 6.6,
                "notes": "Liverpool's population grew to 495,849 by mid‑2022, an increase of 6.6 % over ten years."
            },
            "cultural_engagement": {
                "data_year": "2023-2024",
                "arts_engagement": {
                    "description": "Percentage of adults who engaged with the arts physically in the last 12 months.",
                    "value_percent": 90,
                    "confidence_interval": { "lower": 88, "upper": 92 },
                    "source_table": "Table 78 (Engaged with the arts)"
                },
                "heritage_site_visits": {
                    "description": "Percentage of adults who visited a heritage site in person in the last 12 months.",
                    "value_percent": 62,
                    "confidence_interval": { "lower": 57, "upper": 67 },
                    "source_table": "Table 79 (Visited a heritage site)"
                },
                "museum_gallery_visits": {
                    "description": "Percentage of adults who visited a museum or gallery in person in the last 12 months.",
                    "value_percent": 55,
                    "confidence_interval": { "lower": 51, "upper": 59 },
                    "source_table": "Table 80 (Visited a museum or gallery)"
                },
                "public_library_visits": {
                    "description": "Percentage of adults who visited a public or mobile library in person in the last 12 months.",
                    "value_percent": 25,
                    "confidence_interval": { "lower": 22, "upper": 29 },
                    "source_table": "Table 81 (Visited a public library)"
                }
            },
            "economic_indicators": {
                "data_year": {
                    "inactivity_rate": 2023,
                    "employment_rate": 2023,
                    "unemployment_rate": 2023,
                    "claimant_count": 2024,
                    "gdhi_per_person": 2022,
                    "median_weekly_pay": "April 2024",
                    "gva_per_hour": 2023
                },
                "economic_inactivity_rate": {
                    "description": "Percentage of people aged 16–64 not in work and not seeking work.",
                    "value_percent": 26.1,
                    "confidence_interval": { "lower": 21.4, "upper": 30.8 },
                    "source_table": "Table 1 (Economic inactivity rate)"
                },
                "employment_rate": {
                    "description": "Percentage of people aged 16–64 in paid work.",
                    "value_percent": 67.5,
                    "confidence_interval": { "lower": 62.5, "upper": 72.5 },
                    "source_table": "Table 3 (Employment rate)"
                },
                "modelled_unemployment_rate": {
                    "description": "Percentage of economically active residents who are unemployed and looking for work.",
                    "value_percent": 7.0,
                    "confidence_interval": { "lower": 4.9, "upper": 9.1 },
                    "source_table": "Table 5 (Modelled unemployment rate)"
                },
                "claimant_count_rate": {
                    "description": "Proportion of working‑age residents receiving unemployment‑related benefits.",
                    "value_percent": 6.0,
                    "source_table": "Table 6 (Claimant Count)"
                },
                "gross_disposable_household_income_per_person": {
                    "description": "Amount households can spend or save after taxes and benefits.",
                    "value_gbp": 17408,
                    "units": "£ per person",
                    "source_table": "Table 7 (GDHI per person)"
                },
                "gross_median_weekly_pay": {
                    "description": "Median weekly pay for full‑time employees.",
                    "value_gbp": 582.9,
                    "confidence_interval": { "lower": 548.625, "upper": 617.175 },
                    "units": "£ per week",
                    "source_table": "Table 8 (Gross median weekly pay)"
                },
                "gva_per_hour_worked": {
                    "description": "Gross value added per hour worked—a labour‑productivity measure.",
                    "value_gbp": 37.5,
                    "units": "£ per hour",
                    "source_table": "Table 10 (GVA per hour)"
                }
            }
        }
    ]

def main():
    """Main function to demonstrate multiple city ingestion methods"""
    
    print("🏙️ Multiple City Data Ingestion System")
    print("=" * 50)
    
    # Get sample cities data
    cities_data = get_sample_cities_data()
    
    if not cities_data:
        print("⚠️  No city data found!")
        print("\n📝 To add cities:")
        print("   1. Edit the get_sample_cities_data() function in this file")
        print("   2. Add your city data in the required JSON format")
        print("   3. Run this script again")
        print("\n📋 Required data structure:")
        print("   - city: City name")
        print("   - country: Country name") 
        print("   - population: Year and estimate")
        print("   - cultural_engagement: Arts, heritage, museum, library data")
        print("   - economic_indicators: Employment, income, productivity data")
        return
    
    print(f"📊 Found {len(cities_data)} cities to ingest:")
    for city in cities_data:
        print(f"   • {city['city']} ({city['population']['estimate']:,} population)")
    
    # Initialize ingester
    ingester = CityDataIngester()
    
    # Method 1: Ingest all cities in batch
    print(f"\n🚀 Ingesting all cities in batch...")
    successful, failed = ingester.ingest_multiple_cities(cities_data)
    
    # Close connection
    ingester.close()
    
    print(f"\n✅ Batch ingestion complete!")
    print(f"   Successfully ingested: {successful} cities")
    print(f"   Failed: {failed} cities")
    
    if successful > 0:
        print(f"\n🎯 You can now use these cities in your focus groups:")
        for city in cities_data:
            print(f"   • {city['city']} - /api/city_data/cities/{city['city']}/audience")

if __name__ == "__main__":
    main() 