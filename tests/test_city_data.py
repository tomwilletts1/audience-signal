# test_city_data.py
from src.services.city_audience_service import CityAudienceService

def test_city_data():
    """Test the city data ingestion and retrieval"""
    
    print("🧪 Testing City Data System...")
    
    # Initialize the service
    city_service = CityAudienceService()
    
    # Test 1: List available cities
    print("\n1. Available cities:")
    cities = city_service.list_available_cities()
    print(f"   Found {len(cities)} cities: {cities}")
    
    # Test 2: Get Manchester profile
    print("\n2. Manchester Profile:")
    manchester_profile = city_service.get_city_profile("Manchester")
    if manchester_profile:
        print(f"   Population: {manchester_profile['population_estimate']:,} ({manchester_profile['population_year']})")
        print(f"   Employment Rate: {manchester_profile['employment_rate']}%")
        print(f"   Median Weekly Pay: £{manchester_profile['median_weekly_pay']}")
        print(f"   Arts Engagement: {manchester_profile['arts_engagement_percent']}%")
        print(f"   Museum Visits: {manchester_profile['museum_visits_percent']}%")
    else:
        print("   ❌ No profile found for Manchester")
    
    # Test 3: Create Manchester audience
    print("\n3. Manchester Audience:")
    try:
        manchester_audience = city_service.create_city_audience("Manchester")
        print(f"   Name: {manchester_audience['name']}")
        print(f"   Description: {manchester_audience['description']}")
        print(f"   Personas: {len(manchester_audience['personas'])}")
        for i, persona in enumerate(manchester_audience['personas'], 1):
            print(f"   Persona {i}: {persona[:100]}...")
    except Exception as e:
        print(f"   ❌ Error creating audience: {e}")
    
    # Test 4: Economic summary
    print("\n4. Economic Summary:")
    economic_summary = city_service.get_city_economic_summary("Manchester")
    if economic_summary:
        print(f"   GDHI per person: £{economic_summary['gdhi_per_person']:,}")
        print(f"   GVA per hour: £{economic_summary['gva_per_hour']}")
        print(f"   Unemployment rate: {economic_summary['unemployment_rate']}%")
    else:
        print("   ❌ No economic summary found")
    
    print("\n✅ City data system test completed!")

if __name__ == "__main__":
    test_city_data() 