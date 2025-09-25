"""
Database configuration and initialization
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize SQLAlchemy instance
db = SQLAlchemy()
migrate = Migrate()


def init_app(app):
    """Initialize database with Flask application"""
    
    # Configure SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config.get(
        'DATABASE_URL', 
        'sqlite:///contract_analyzer.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    return db