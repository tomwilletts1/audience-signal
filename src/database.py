import sqlite3
from src.utils.logger import app_logger

DATABASE_PATH = "audience_engine.db"

def get_db_connection():
    """Creates and returns a new database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """Creates all necessary database tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        app_logger.info("Checking and creating database tables...")

        # Audience Definitions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audiences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            criteria TEXT,
            owner_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Persona Profiles
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS personas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audience_id INTEGER,
            demographics TEXT,
            embedding_id TEXT,
            description TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (audience_id) REFERENCES audiences (id)
        );
        """)
        
        # History Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            message TEXT,
            image INTEGER,
            personas TEXT,
            results TEXT
        );
        """)

        conn.commit()
        app_logger.info("Database tables created successfully.")
    except Exception as e:
        app_logger.error(f"Error creating database tables: {e}", exc_info=True)
    finally:
        conn.close()
