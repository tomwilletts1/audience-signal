from flask import Flask, send_from_directory
from flask_cors import CORS
from src.config import config
from src.utils.logger import app_logger
from src.database import create_tables, get_db_connection

# --- Consolidated Service Imports ---
from src.services.embedding_service import EmbeddingService
from src.services.data_service import DataService
from src.services.persona_service import PersonaService
from src.services.audience_service import AudienceService
from src.services.content_test_service import ContentTestService
from src.services.ai_service import AIService
from src.utils.history_manager import HistoryManager

# --- Blueprint Imports ---
from src.routes.api import create_api_blueprint
from src.routes.focus_group import create_focus_group_blueprint
from src.routes.city_data import create_city_data_blueprint

# --- App Initialization ---
app_logger.info("Application startup sequence initiated.")

# 1. Initialize Database
create_tables()

# 2. Initialize Services (in dependency order)
app_logger.info("Initializing services...")
db_connection = get_db_connection()

# Core services
embedding_service = EmbeddingService()
data_service = DataService()
ai_service = AIService()
history_manager = HistoryManager()

# Business logic services
persona_service = PersonaService(db_connection, embedding_service, data_service)
audience_service = AudienceService(db_connection, persona_service)
content_test_service = ContentTestService(audience_service, persona_service)

app_logger.info("All services initialized.")

# 3. Initialize Flask App
app = Flask(__name__, static_folder=config['default'].FRONTEND_DIR)
CORS(app, resources={r"/api/*": {"origins": config['default'].CORS_ORIGINS}})
app_logger.info("Flask app configured with CORS.")

# 4. Register Blueprints (passing services as dependencies)
app_logger.info("Registering blueprints...")
app.register_blueprint(create_api_blueprint(history_manager, audience_service, content_test_service, data_service))
app.register_blueprint(create_focus_group_blueprint(audience_service, data_service))
app.register_blueprint(create_city_data_blueprint())
app_logger.info("All blueprints registered.")

# --- Frontend Serving Routes ---
@app.route('/')
def serve_frontend_main():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/focus-group')
def serve_focus_group():
    return send_from_directory(app.static_folder, 'focus_group_advanced.html')

@app.route('/focus-group-advanced')
def serve_focus_group_advanced():
    return send_from_directory(app.static_folder, 'focus_group_advanced.html')

@app.route('/audiences')
def serve_audiences():
    return send_from_directory(app.static_folder, 'audiences.html')

@app.route('/polling')
def serve_polling():
    return send_from_directory(app.static_folder, 'polling.html')

@app.route('/data')
def serve_data():
    return send_from_directory(app.static_folder, 'data.html')

@app.route('/history')
def serve_history():
    return send_from_directory(app.static_folder, 'history.html')

@app.route('/test-content')
def serve_test_content():
    return send_from_directory(app.static_folder, 'test-content.html')

# --- Main Execution ---
if __name__ == '__main__':
    app_logger.info("Starting Flask app on 0.0.0.0:5000")
    app.run(
        host=config['default'].HOST,
        port=config['default'].PORT,
        debug=config['default'].DEBUG
    ) 