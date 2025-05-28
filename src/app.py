from flask import Flask, send_from_directory
from flask_cors import CORS
from config import config
from utils.history_manager import HistoryManager
from utils.logger import app_logger

# Import blueprint factories
from routes.analyze import create_analyze_blueprint
from routes.history import create_history_blueprint
from routes.presets import create_presets_blueprint
from routes.summary import create_summary_blueprint
from routes.focus_group import create_focus_group_blueprint

# Ensure openai_service is imported to configure API key at startup
try:
    import services.openai_service # This will run the API key configuration
    app_logger.info("OpenAI service imported, API key should be configured if present.")
except ImportError as e:
    app_logger.error(f"Could not import openai_service for initial API key config: {e}")
except Exception as e:
    app_logger.error(f"Error during initial openai_service import: {e}")

# Initialize Flask app with configuration
app_logger.info("Flask app initialization started.")
app = Flask(__name__, static_folder=config['default'].FRONTEND_DIR)
CORS(app, resources={r"/api/*": {"origins": config['default'].CORS_ORIGINS}})

# Initialize HistoryManager
history_manager = HistoryManager()
app_logger.info("HistoryManager initialized.")

# Create and register blueprints
analyze_bp = create_analyze_blueprint(history_manager)
app.register_blueprint(analyze_bp)
app_logger.info("Analyze blueprint registered.")

history_bp = create_history_blueprint(history_manager)
app.register_blueprint(history_bp)
app_logger.info("History blueprint registered.")

presets_bp = create_presets_blueprint()
app.register_blueprint(presets_bp)
app_logger.info("Presets blueprint registered.")

summary_bp = create_summary_blueprint()
app.register_blueprint(summary_bp)
app_logger.info("Summary blueprint registered.")

focus_group_bp = create_focus_group_blueprint()
app.register_blueprint(focus_group_bp)
app_logger.info("Focus Group blueprint registered.")

# --- Frontend Serving Routes ---

# Route for the main page (index.html)
@app.route('/')
def serve_frontend_main():
    return send_from_directory(app.static_folder, 'index.html')

# Route for the new focus group tool page
@app.route('/focus-group-tool')
def focus_group_tool():
    """Serve the focus group tool page."""
    return send_from_directory(app.static_folder, 'focus_group_tool.html')

# Route for the advanced focus group tool page
@app.route('/focus-group-advanced')
def focus_group_advanced():
    """Serve the advanced focus group tool page."""
    return send_from_directory(app.static_folder, 'focus_group_advanced.html')

# Route for other static files (CSS, JS, images) in the frontend directory
@app.route('/<path:filename>')
def serve_static_files_in_frontend(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    app_logger.info(f"Starting Flask app on {config['default'].HOST}:{config['default'].PORT} with debug={config['default'].DEBUG}")
    app.run(
        debug=config['default'].DEBUG,
        host=config['default'].HOST,
        port=int(config['default'].PORT)
    ) 