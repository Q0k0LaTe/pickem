from flask import Blueprint, jsonify, request, redirect, url_for, current_app
from src.models.user import User, db
from src.steam_auth import SteamOpenID, JWTManager, ViewerPassManager
import logging
from datetime import datetime, timedelta
import os
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# Initialize Steam OpenID with configuration
steam_openid = SteamOpenID(
    api_key=os.getenv('STEAM_API_KEY'),
    return_url=os.getenv('STEAM_RETURN_URL', 'http://localhost:3000/auth/steam/callback')
)

@auth_bp.route('/steam/login', methods=['GET'])
def steam_login():
    """Initiate Steam OpenID authentication"""
    try:
        # Get return URL from query parameters
        return_to = request.args.get('return_to')
        
        # Generate Steam authentication URL
        auth_url = steam_openid.get_auth_url(return_to)
        
        return jsonify({
            'success': True,
            'data': {
                'auth_url': auth_url,
                'message': 'Redirect to Steam for authentication'
            }
        })
        
    except Exception as e:
        logger.error(f"Error initiating Steam login: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to initiate Steam authentication'
        }), 500

@auth_bp.route('/steam/callback', methods=['GET', 'POST'])
def steam_callback():
    """Handle Steam OpenID authentication callback"""
    try:
        # Get all query parameters from the callback
        auth_params = request.args.to_dict()
        
        # Verify the Steam authentication response
        steam_id = steam_openid.verify_auth_response(auth_params)
        
        if not steam_id:
            return jsonify({
                'success': False,
                'error': 'Steam authentication verification failed'
            }), 400
        
        # Get user information from Steam
        steam_user_info = steam_openid.get_user_info(steam_id)
        
        if not steam_user_info:
            return jsonify({
                'success': False,
                'error': 'Failed to retrieve user information from Steam'
            }), 500
        
        # Find or create user in database
        user = User.query.filter_by(steam_id=steam_id).first()
        
        if not user:
            # Create new user
            user = User(
                steam_id=steam_id,
                username=steam_user_info['username'],
                avatar_url=steam_user_info['avatar_url'],
                profile_url=steam_user_info['profile_url'],
                real_name=steam_user_info.get('real_name', ''),
                country_code=steam_user_info.get('country_code', ''),
                viewer_pass_tokens=ViewerPassManager.get_user_tokens(steam_id)
            )
            db.session.add(user)
        else:
            # Update existing user information
            user.username = steam_user_info['username']
            user.avatar_url = steam_user_info['avatar_url']
            user.profile_url = steam_user_info['profile_url']
            user.real_name = steam_user_info.get('real_name', '')
            user.country_code = steam_user_info.get('country_code', '')
            user.viewer_pass_tokens = ViewerPassManager.get_user_tokens(steam_id)
            user.last_login = datetime.utcnow()
        
        db.session.commit()
        
        # Create JWT tokens
        tokens = JWTManager.create_tokens(
            user_id=str(user.id),
            additional_claims={
                'steam_id': steam_id,
                'username': user.username,
                'viewer_pass_tokens': user.viewer_pass_tokens
            }
        )
        
        logger.info(f"User {user.username} ({steam_id}) authenticated successfully")
        
        return jsonify({
            'success': True,
            'data': {
                'user': {
                    'id': str(user.id),
                    'steam_id': user.steam_id,
                    'username': user.username,
                    'avatar_url': user.avatar_url,
                    'profile_url': user.profile_url,
                    'real_name': user.real_name,
                    'country_code': user.country_code,
                    'viewer_pass_tokens': user.viewer_pass_tokens,
                    'created_at': user.created_at.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None
                },
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token'],
                'expires_in': 3600  # 1 hour
            }
        })
        
    except Exception as e:
        logger.error(f"Error in Steam callback: {e}")
        return jsonify({
            'success': False,
            'error': 'Authentication callback processing failed'
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """Refresh access token using refresh token"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user from database to ensure they still exist
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Create new access token
        new_access_token = JWTManager.refresh_access_token(current_user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'access_token': new_access_token,
                'expires_in': 3600  # 1 hour
            }
        })
        
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return jsonify({
            'success': False,
            'error': 'Token refresh failed'
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        current_user_id = get_jwt_identity()
        
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Update viewer pass tokens from Steam
        user.viewer_pass_tokens = ViewerPassManager.get_user_tokens(user.steam_id)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'user': {
                    'id': str(user.id),
                    'steam_id': user.steam_id,
                    'username': user.username,
                    'avatar_url': user.avatar_url,
                    'profile_url': user.profile_url,
                    'real_name': user.real_name,
                    'country_code': user.country_code,
                    'viewer_pass_tokens': user.viewer_pass_tokens,
                    'created_at': user.created_at.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve profile'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (invalidate token)"""
    try:
        # In a production system, you would add the token to a blacklist
        # For now, just return success
        
        return jsonify({
            'success': True,
            'data': {
                'message': 'Logged out successfully'
            }
        })
        
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        return jsonify({
            'success': False,
            'error': 'Logout failed'
        }), 500

@auth_bp.route('/validate', methods=['GET'])
@jwt_required()
def validate_token():
    """Validate current token and return user info"""
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'valid': True,
                'user_id': current_user_id,
                'steam_id': claims.get('steam_id'),
                'username': claims.get('username'),
                'viewer_pass_tokens': claims.get('viewer_pass_tokens'),
                'expires_at': claims.get('exp')
            }
        })
        
    except Exception as e:
        logger.error(f"Error validating token: {e}")
        return jsonify({
            'success': False,
            'error': 'Token validation failed'
        }), 500

# Mock login endpoint for development
@auth_bp.route('/mock-login', methods=['POST'])
def mock_login():
    """Mock login endpoint for development and testing"""
    try:
        data = request.get_json() or {}
        steam_id = data.get('steam_id', '76561198000000001')
        
        # Get mock user info
        steam_user_info = steam_openid._get_mock_user_info(steam_id)
        
        # Find or create user
        user = User.query.filter_by(steam_id=steam_id).first()
        
        if not user:
            user = User(
                steam_id=steam_id,
                username=steam_user_info['username'],
                avatar_url=steam_user_info['avatar_url'],
                profile_url=steam_user_info['profile_url'],
                real_name=steam_user_info.get('real_name', ''),
                country_code=steam_user_info.get('country_code', ''),
                viewer_pass_tokens=ViewerPassManager.get_user_tokens(steam_id)
            )
            db.session.add(user)
        else:
            user.last_login = datetime.utcnow()
        
        db.session.commit()
        
        # Create JWT tokens
        tokens = JWTManager.create_tokens(
            user_id=str(user.id),
            additional_claims={
                'steam_id': steam_id,
                'username': user.username,
                'viewer_pass_tokens': user.viewer_pass_tokens
            }
        )
        
        return jsonify({
            'success': True,
            'data': {
                'user': {
                    'id': str(user.id),
                    'steam_id': user.steam_id,
                    'username': user.username,
                    'avatar_url': user.avatar_url,
                    'profile_url': user.profile_url,
                    'real_name': user.real_name,
                    'country_code': user.country_code,
                    'viewer_pass_tokens': user.viewer_pass_tokens,
                    'created_at': user.created_at.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None
                },
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token'],
                'expires_in': 3600
            }
        })
        
    except Exception as e:
        logger.error(f"Error in mock login: {e}")
        return jsonify({
            'success': False,
            'error': 'Mock login failed'
        }), 500

@auth_bp.route('/steam/status', methods=['GET'])
def steam_status():
    """Get Steam authentication status and configuration"""
    return jsonify({
        'success': True,
        'data': {
            'steam_api_configured': bool(os.getenv('STEAM_API_KEY')),
            'return_url': steam_openid.return_url,
            'mock_mode': not bool(os.getenv('STEAM_API_KEY')),
            'available_endpoints': [
                '/auth/steam/login',
                '/auth/steam/callback',
                '/auth/refresh',
                '/auth/profile',
                '/auth/logout',
                '/auth/validate',
                '/auth/mock-login'
            ]
        }
    })

