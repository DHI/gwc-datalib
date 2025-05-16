import requests
from decouple import config as decouple_config
from datetime import datetime, timedelta
from getpass import getpass

# Global variables to store the token and its expiration time
access_token = None
token_expiry = None

def get_auth0_token():
    """Authenticate with Auth0 and retrieve an access token. If the token is expired or doesn't exist, prompt the user for credentials."""
    global access_token, token_expiry

    if access_token and token_expiry and datetime.now() < token_expiry:
        # If the token is still valid, return it
        return access_token
    
    # Load credentials from the .env file
    username = decouple_config("API_USER", default=None)
    password = decouple_config("API_PASSWORD", default=None)

    if not username or not password:
        # Prompt the user for their username and password
        username = input("Enter your Auth0 username: ")
        password = getpass("Enter your Auth0 password: ")

    url = f"https://{decouple_config('AUTH0_DOMAIN')}/oauth/token"

    payload = {
        "grant_type": "password",
        "client_id": decouple_config("AUTH0_CLIENT_ID"),
        "client_secret": decouple_config("AUTH0_CLIENT_SECRET"),
        "username": username,
        "password": password,
        "audience": decouple_config("API_AUDIENCE"),
        "scope": "openid email profile",
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()
    response_data = response.json()
    access_token = response_data.get("access_token")

    # Calculate token expiry (Auth0 tokens typically last 24 hours, but this can vary)
    expires_in = response_data.get(
        "expires_in", 86400
    )  # Default to 24 hours if not provided
    token_expiry = datetime.now() + timedelta(seconds=expires_in)

    return access_token
