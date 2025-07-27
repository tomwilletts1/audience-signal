# src/routes/city_data.py
from flask import Blueprint, request, jsonify
from src.services.data_service import DataService
from src.utils.logger import app_logger

def create_city_data_blueprint():
    bp = Blueprint('city_data', __name__, url_prefix='/api/city_data')
    
    data_service = DataService()
    
    @bp.route('/cities', methods=['GET'])
    def list_cities():
        """Get list of all available cities"""
        try:
            cities = data_service.get_all_cities()
            return jsonify({
                'status': 'success',
                'cities': cities,
                'count': len(cities)
            })
        except Exception as e:
            app_logger.error(f"Error listing cities: {e}", exc_info=True)
            return jsonify({
                'status': 'error',
                'error': 'Failed to retrieve cities'
            }), 500
    
    @bp.route('/cities/<city_name>', methods=['GET'])
    def get_city_details(city_name):
        """Get detailed information about a specific city"""
        try:
            city_profile = data_service.get_city_profile(city_name)
            
            if not city_profile:
                return jsonify({
                    'status': 'error',
                    'error': f'City "{city_name}" not found'
                }), 404
            
            return jsonify({
                'status': 'success',
                'city': city_profile
            })
        except Exception as e:
            app_logger.error(f"Error getting city details for {city_name}: {e}", exc_info=True)
            return jsonify({
                'status': 'error',
                'error': f'Failed to retrieve details for city "{city_name}"'
            }), 500
    
    @bp.route('/cities/<city_name>/audience', methods=['GET'])
    def get_city_audience(city_name):
        """Get audience personas for a specific city"""
        try:
            city_audience = data_service.create_city_audience(city_name)
            return jsonify({
                'status': 'success',
                'audience': city_audience
            })
        except ValueError as ve:
            return jsonify({
                'status': 'error',
                'error': str(ve)
            }), 404
        except Exception as e:
            app_logger.error(f"Error creating city audience for {city_name}: {e}", exc_info=True)
            return jsonify({
                'status': 'error',
                'error': f'Failed to create audience for city "{city_name}"'
            }), 500
    
    @bp.route('/cities/<city_name>/demographics', methods=['GET'])
    def get_city_demographics(city_name):
        """Get demographic data for a specific city"""
        try:
            # Use ONS data for demographic sampling
            demographics = data_service.sample_ons_profile(city_name)
            summary_stats = data_service.get_ons_summary_stats(city_name)
            
            return jsonify({
                'status': 'success',
                'demographics': {
                    'sample_profile': demographics,
                    'summary_stats': summary_stats
                }
            })
        except Exception as e:
            app_logger.error(f"Error getting demographics for {city_name}: {e}", exc_info=True)
            return jsonify({
                'status': 'error',
                'error': f'Failed to retrieve demographics for city "{city_name}"'
            }), 500
    
    @bp.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint for the city data service"""
        try:
            # Test database connectivity by getting city count
            cities = data_service.get_all_cities()
            return jsonify({
                'status': 'healthy',
                'message': 'City data service is operational',
                'available_cities': len(cities),
                'timestamp': app_logger.handlers[0].formatter.formatTime(
                    app_logger.makeRecord('test', 0, '', 0, '', (), None)
                )
            })
        except Exception as e:
            app_logger.error(f"Health check failed: {e}", exc_info=True)
            return jsonify({
                'status': 'unhealthy',
                'error': 'City data service is not operational'
            }), 500
    
    return bp 