import os
import json
import requests
from urllib.parse import urlencode
import secrets
import base64
import hashlib

# Constants for Google OAuth
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USER_INFO_URL = 'https://www.googleapis.com/oauth2/v1/userinfo'

class GoogleAuthError(Exception):
    """Exception raised for errors in the Google Auth process."""
    pass

def get_auth_url(redirect_uri):
    """
    Generate the Google OAuth authorization URL
    
    Args:
        redirect_uri: The URI to redirect to after authentication
        
    Returns:
        str: Authentication URL for Google OAuth
    """
    if not GOOGLE_CLIENT_ID:
        raise GoogleAuthError("Google Client ID is not configured")
    
    # Generate a random state value for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Generate PKCE code verifier and challenge
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip('=')
    
    # Store these values in a state dictionary
    auth_state = {
        'state': state,
        'code_verifier': code_verifier,
        'redirect_uri': redirect_uri
    }
    
    # Parameters for the authorization request
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return auth_url, auth_state

def exchange_code_for_token(code, code_verifier, redirect_uri):
    """
    Exchange an authorization code for an access token
    
    Args:
        code: Authorization code from Google
        code_verifier: PKCE code verifier used in the authorization request
        redirect_uri: The redirect URI used in the authorization request
        
    Returns:
        dict: Token response from Google
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise GoogleAuthError("Google credentials are not configured")
    
    token_params = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'code': code,
        'code_verifier': code_verifier,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri
    }
    
    response = requests.post(GOOGLE_TOKEN_URL, data=token_params)
    
    if response.status_code != 200:
        raise GoogleAuthError(f"Failed to exchange code for token: {response.text}")
    
    return response.json()

def get_user_info(access_token):
    """
    Get user information from Google using the access token
    
    Args:
        access_token: The access token from Google
        
    Returns:
        dict: User information from Google
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(GOOGLE_USER_INFO_URL, headers=headers)
    
    if response.status_code != 200:
        raise GoogleAuthError(f"Failed to get user info: {response.text}")
    
    return response.json()

def validate_state(received_state, stored_state):
    """
    Validate that the received state matches the stored state
    
    Args:
        received_state: State parameter received in the callback
        stored_state: State parameter stored during the auth request
        
    Returns:
        bool: True if the states match, else raises an exception
    """
    if received_state != stored_state:
        raise GoogleAuthError("Invalid state parameter, possible CSRF attack")
    return True