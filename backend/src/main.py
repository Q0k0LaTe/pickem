import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.matches import matches_bp
from src.routes.optimization import optimization_bp
from src.routes.picks import picks_bp
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'pickem-pro-secret-key-change-in-production')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600  # 1 hour
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 2592000  # 30 days

# Database configuration - PostgreSQL with SQLite fallback
database_url = os.getenv('DATABASE_URL')
if database_url:
    # Production database URL
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Try PostgreSQL first, fallback to SQLite for development
    try:
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'pickem_pro')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', 'password')
        
        # Test PostgreSQL connection
        import psycopg2
        test_conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database='postgres',  # Connect to default database first
            user=db_user,
            password=db_password
        )
        test_conn.close()
        
        app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        logger.info("Using PostgreSQL database")
        
    except Exception as e:
        # Fallback to SQLite for development
        logger.warning(f"PostgreSQL not available ({str(e)}), falling back to SQLite")
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pickem_pro.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Initialize extensions
CORS(app, origins="*")  # Allow all origins for development
jwt = JWTManager(app)
db.init_app(app)

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(matches_bp, url_prefix='/api')
app.register_blueprint(optimization_bp, url_prefix='/api')
app.register_blueprint(picks_bp, url_prefix='/api')

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'success': False,
        'error': 'Token has expired',
        'code': 'TOKEN_EXPIRED'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'success': False,
        'error': 'Invalid token',
        'code': 'INVALID_TOKEN'
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        'success': False,
        'error': 'Authorization token is required',
        'code': 'MISSING_TOKEN'
    }), 401

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = 'unhealthy'
    
    return jsonify({
        'success': True,
        'data': {
            'status': 'healthy',
            'database': db_status,
            'version': '1.0.0',
            'environment': os.getenv('FLASK_ENV', 'development')
        }
    })

# API info endpoint
@app.route('/api/info', methods=['GET'])
def api_info():
    """API information endpoint"""
    return jsonify({
        'success': True,
        'data': {
            'name': 'PickEm Pro API',
            'version': '1.0.0',
            'description': 'Counter-Strike Major Pick\'Em prediction API',
            'endpoints': {
                'auth': '/api/auth/*',
                'matches': '/api/matches/*',
                'optimization': '/api/optimize/*',
                'picks': '/api/picks/*',
                'users': '/api/users/*'
            },
            'documentation': 'https://github.com/your-repo/pickem-pro'
        }
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'code': 'NOT_FOUND'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'code': 'INTERNAL_ERROR'
    }), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'code': 'BAD_REQUEST'
    }), 400

# Static file serving for frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return jsonify({
            'success': False,
            'error': 'Static folder not configured'
        }), 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            # Return API info if no frontend is available
            return jsonify({
                'success': True,
                'message': 'PickEm Pro API is running',
                'api_info': '/api/info',
                'health_check': '/api/health'
            })

# Database initialization
def init_database():
    """Initialize database tables"""
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Add some sample data for development
            if os.getenv('FLASK_ENV') == 'development':
                add_sample_data()
                
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")

def add_sample_data():
    """Add sample data for development"""
    try:
        from src.models.user import User, Match, Odds
        from datetime import datetime, timedelta
        
        # Check if sample data already exists
        if User.query.first():
            logger.info("Sample data already exists, skipping...")
            return
        
        # Create sample users
        sample_users = [
            User(
                steam_id='76561198000000001',
                username='TestUser1',
                avatar_url='https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/default.jpg',
                viewer_pass_tokens=3
            ),
            User(
                steam_id='76561198000000002',
                username='TestUser2',
                avatar_url='https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/default.jpg',
                viewer_pass_tokens=5
            )
        ]
        
        for user in sample_users:
            db.session.add(user)
        
        # Create sample matches
        sample_matches = [
            Match(
                external_id='swiss_1_1',
                team_a='G2',
                team_b='FaZe',
                stage='swiss',
                round_number=1,
                scheduled_time=datetime.utcnow() + timedelta(hours=1),
                status='upcoming'
            ),
            Match(
                external_id='swiss_1_2',
                team_a='NAVI',
                team_b='Astralis',
                stage='swiss',
                round_number=1,
                scheduled_time=datetime.utcnow() + timedelta(hours=2),
                status='upcoming'
            ),
            Match(
                external_id='swiss_1_3',
                team_a='Vitality',
                team_b='Team Liquid',
                stage='swiss',
                round_number=1,
                scheduled_time=datetime.utcnow() + timedelta(hours=3),
                status='upcoming'
            )
        ]
        
        for match in sample_matches:
            db.session.add(match)
        
        db.session.commit()
        
        # Add sample odds
        for match in sample_matches:
            odds = Odds(
                match_id=match.id,
                source='mock_data',
                team_a_win_prob=0.6,
                team_b_win_prob=0.4,
                raw_data={'generated': True}
            )
            db.session.add(odds)
        
        db.session.commit()
        logger.info("Sample data added successfully")
        
    except Exception as e:
        logger.error(f"Failed to add sample data: {str(e)}")
        db.session.rollback()

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Run the application
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"Starting PickEm Pro API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)

