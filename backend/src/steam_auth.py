import requests
import urllib.parse
import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask_jwt_extended import create_access_token, create_refresh_token

logger = logging.getLogger(__name__)

class SteamOpenID:
    """Steam OpenID authentication service"""
    
    STEAM_OPENID_URL = 'https://steamcommunity.com/openid/login'
    STEAM_API_URL = 'https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/'
    
    def __init__(self, api_key: Optional[str] = None, return_url: str = None):
        self.api_key = api_key
        self.return_url = return_url or 'http://localhost:3000/auth/steam/callback'
    
    def get_auth_url(self, return_to: str = None) -> str:
        """Generate Steam OpenID authentication URL"""
        params = {
            'openid.ns': 'http://specs.openid.net/auth/2.0',
            'openid.mode': 'checkid_setup',
            'openid.return_to': return_to or self.return_url,
            'openid.realm': self._get_realm(),
            'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
            'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select'
        }
        
        return f"{self.STEAM_OPENID_URL}?{urllib.parse.urlencode(params)}"
    
    def verify_auth_response(self, args: Dict[str, Any]) -> Optional[str]:
        """Verify Steam OpenID authentication response and return Steam ID"""
        try:
            # Check if response contains required OpenID parameters
            if 'openid.mode' not in args or args['openid.mode'] != 'id_res':
                logger.warning("Invalid OpenID mode in response")
                return None
            
            # Prepare verification parameters
            params = dict(args)
            params['openid.mode'] = 'check_authentication'
            
            # Verify with Steam
            response = requests.post(self.STEAM_OPENID_URL, data=params, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Steam verification failed with status {response.status_code}")
                return None
            
            # Check if verification was successful
            if 'is_valid:true' not in response.text:
                logger.warning("Steam verification returned invalid")
                return None
            
            # Extract Steam ID from claimed_id
            claimed_id = args.get('openid.claimed_id', '')
            steam_id_match = re.search(r'/id/(\d+)/?$', claimed_id)
            
            if not steam_id_match:
                logger.error(f"Could not extract Steam ID from claimed_id: {claimed_id}")
                return None
            
            steam_id = steam_id_match.group(1)
            logger.info(f"Successfully verified Steam ID: {steam_id}")
            return steam_id
            
        except requests.RequestException as e:
            logger.error(f"Network error during Steam verification: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during Steam verification: {e}")
            return None
    
    def get_user_info(self, steam_id: str) -> Optional[Dict[str, Any]]:
        """Get user information from Steam Web API"""
        if not self.api_key:
            logger.warning("No Steam API key configured, using mock data")
            return self._get_mock_user_info(steam_id)
        
        try:
            params = {
                'key': self.api_key,
                'steamids': steam_id,
                'format': 'json'
            }
            
            response = requests.get(self.STEAM_API_URL, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Steam API request failed with status {response.status_code}")
                return self._get_mock_user_info(steam_id)
            
            data = response.json()
            players = data.get('response', {}).get('players', [])
            
            if not players:
                logger.warning(f"No player data found for Steam ID: {steam_id}")
                return self._get_mock_user_info(steam_id)
            
            player = players[0]
            return {
                'steam_id': player.get('steamid'),
                'username': player.get('personaname', f'User_{steam_id[-4:]}'),
                'avatar_url': player.get('avatarfull', ''),
                'profile_url': player.get('profileurl', ''),
                'real_name': player.get('realname', ''),
                'country_code': player.get('loccountrycode', ''),
                'state_code': player.get('locstatecode', ''),
                'city_id': player.get('loccityid', 0),
                'time_created': player.get('timecreated', 0),
                'profile_state': player.get('communityvisibilitystate', 1),
                'last_logoff': player.get('lastlogoff', 0)
            }
            
        except requests.RequestException as e:
            logger.error(f"Network error fetching Steam user info: {e}")
            return self._get_mock_user_info(steam_id)
        except Exception as e:
            logger.error(f"Unexpected error fetching Steam user info: {e}")
            return self._get_mock_user_info(steam_id)
    
    def _get_realm(self) -> str:
        """Get the realm for OpenID authentication"""
        if self.return_url:
            parsed = urllib.parse.urlparse(self.return_url)
            return f"{parsed.scheme}://{parsed.netloc}"
        return "http://localhost:3000"
    
    def _get_mock_user_info(self, steam_id: str) -> Dict[str, Any]:
        """Generate mock user info for development"""
        mock_users = {
            '76561198000000001': {
                'steam_id': steam_id,
                'username': 'TestUser1',
                'avatar_url': 'https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/default.jpg',
                'profile_url': f'https://steamcommunity.com/profiles/{steam_id}/',
                'real_name': 'Test User One',
                'country_code': 'US',
                'state_code': 'CA',
                'city_id': 0,
                'time_created': int(datetime.now().timestamp()) - 86400 * 365,
                'profile_state': 3,
                'last_logoff': int(datetime.now().timestamp()) - 3600
            },
            '76561198000000002': {
                'steam_id': steam_id,
                'username': 'TestUser2',
                'avatar_url': 'https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/default.jpg',
                'profile_url': f'https://steamcommunity.com/profiles/{steam_id}/',
                'real_name': 'Test User Two',
                'country_code': 'GB',
                'state_code': '',
                'city_id': 0,
                'time_created': int(datetime.now().timestamp()) - 86400 * 200,
                'profile_state': 3,
                'last_logoff': int(datetime.now().timestamp()) - 7200
            }
        }
        
        return mock_users.get(steam_id, {
            'steam_id': steam_id,
            'username': f'User_{steam_id[-4:]}',
            'avatar_url': 'https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/default.jpg',
            'profile_url': f'https://steamcommunity.com/profiles/{steam_id}/',
            'real_name': '',
            'country_code': '',
            'state_code': '',
            'city_id': 0,
            'time_created': int(datetime.now().timestamp()) - 86400 * 100,
            'profile_state': 3,
            'last_logoff': int(datetime.now().timestamp()) - 3600
        })


class JWTManager:
    """Enhanced JWT token management"""
    
    @staticmethod
    def create_tokens(user_id: str, additional_claims: Dict[str, Any] = None) -> Dict[str, str]:
        """Create access and refresh tokens for a user"""
        claims = additional_claims or {}
        
        access_token = create_access_token(
            identity=user_id,
            additional_claims=claims,
            expires_delta=timedelta(hours=1)
        )
        
        refresh_token = create_refresh_token(
            identity=user_id,
            additional_claims=claims,
            expires_delta=timedelta(days=30)
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }
    
    @staticmethod
    def refresh_access_token(current_user_id: str) -> str:
        """Create a new access token from a refresh token"""
        return create_access_token(
            identity=current_user_id,
            expires_delta=timedelta(hours=1)
        )
    
    @staticmethod
    def validate_token_claims(required_claims: Dict[str, Any] = None) -> bool:
        """Validate additional claims in the current token"""
        if not required_claims:
            return True
        
        # This would be implemented with flask-jwt-extended's get_jwt()
        # For now, just return True
        return True


class ViewerPassManager:
    """Manage CS2 Viewer Pass tokens"""
    
    @staticmethod
    def get_user_tokens(steam_id: str) -> int:
        """Get the number of viewer pass tokens for a user"""
        # In a real implementation, this would check the user's Steam inventory
        # or connect to Valve's API to get actual viewer pass token count
        
        # For development, return mock data based on Steam ID
        mock_tokens = {
            '76561198000000001': 3,
            '76561198000000002': 5,
            '76561198000000003': 1,
        }
        
        # Default to 3 tokens for unknown users
        return mock_tokens.get(steam_id, 3)
    
    @staticmethod
    def validate_token_usage(steam_id: str, required_tokens: int = 1) -> bool:
        """Validate if user has enough tokens for an operation"""
        available_tokens = ViewerPassManager.get_user_tokens(steam_id)
        return available_tokens >= required_tokens
    
    @staticmethod
    def consume_tokens(steam_id: str, tokens_to_consume: int = 1) -> bool:
        """Consume viewer pass tokens (mock implementation)"""
        # In a real implementation, this would interact with Valve's systems
        # For development, just validate the user has enough tokens
        return ViewerPassManager.validate_token_usage(steam_id, tokens_to_consume)

