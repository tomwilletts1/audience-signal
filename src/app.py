from flask import Flask, send_from_directory
from flask_cors import CORS
from src.config import config
from src.utils.logger import app_logger
from src.database import create_tables, get_db_connection

# --- Service Imports ---
from src.services.embedding_service import EmbeddingService
from src.services.ons_data_service import ONSDataService
from src.services.persona_service import PersonaService
from src.services.audience_service import AudienceService
from src.services.client_data_service import ClientDataService
from src.utils.history_manager import HistoryManager
from src.services.content_test_service import ContentTestService

# --- Blueprint Imports ---
from src.routes.analyze import create_analyze_blueprint
from src.routes.history import create_history_blueprint
from src.routes.presets import create_presets_blueprint
from src.routes.summary import create_summary_blueprint
from src.routes.focus_group import create_focus_group_blueprint
from src.routes.audience import create_audience_blueprint
from src.routes.test_content import create_test_content_blueprint
from src.routes.client_data import create_client_data_blueprint
# TODO: Add imports for new route blueprints (audience, polling, etc.)

# --- App Initialization ---
app_logger.info("Application startup sequence initiated.")

# 1. Initialize Database
create_tables()

# 2. Initialize Services (in dependency order)
app_logger.info("Initializing services...")
db_connection = get_db_connection() # For services that need it

embedding_service = EmbeddingService()
ons_data_service = ONSDataService()
persona_service = PersonaService(db_connection, embedding_service, ons_data_service)
audience_service = AudienceService(db_connection, persona_service)
client_data_service = ClientDataService(db_connection, audience_service)
content_test_service = ContentTestService(audience_service, persona_service)
history_manager = HistoryManager() # Now uses get_db_connection internally
app_logger.info("All services initialized.")


# 3. Initialize Flask App
app = Flask(__name__, static_folder=config['default'].FRONTEND_DIR)
CORS(app, resources={r"/api/*": {"origins": config['default'].CORS_ORIGINS}})
app_logger.info("Flask app configured with CORS.")

# 4. Register Blueprints (passing services as dependencies)
app_logger.info("Registering blueprints...")
app.register_blueprint(create_analyze_blueprint(history_manager))
app.register_blueprint(create_history_blueprint(history_manager))
app.register_blueprint(create_presets_blueprint())
app.register_blueprint(create_summary_blueprint())
app.register_blueprint(create_focus_group_blueprint(audience_service))
app.register_blueprint(create_audience_blueprint(audience_service))
app.register_blueprint(create_test_content_blueprint(content_test_service))
app.register_blueprint(create_client_data_blueprint(client_data_service))
# TODO: Register new blueprints for audience, polling, etc.
app_logger.info("All blueprints registered.")

# --- Frontend Serving Routes ---
@app.route('/')
def serve_frontend_main():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_frontend_other(path):
    if '.' not in path:
        path = f'{path}.html'
    
    # Security: Ensure path is within the static folder
    from werkzeug.security import safe_join
    import os
    try:
        safe_path = safe_join(app.static_folder, path)
        if os.path.isfile(safe_path):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html'), 404
    except:
        return send_from_directory(app.static_folder, 'index.html'), 404

@app.route('/focus-group-advanced')
def serve_focus_group():
    return send_from_directory(app.static_folder, 'focus_group_advanced.html')

@app.route('/data.html')
def serve_data():
    return send_from_directory(app.static_folder, 'data.html')

# --- Main Execution ---
if __name__ == '__main__':
    app_logger.info(f"Starting Flask app on {config['default'].HOST}:{config['default'].PORT}")
    app.run(
        debug=config['default'].DEBUG,
        host=config['default'].HOST,
        port=int(config['default'].PORT)
    ) 