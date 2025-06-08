import requests
import streamlit as st
import sys
import os

# Add parent directory to path to import azure_keyvault
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from azure_keyvault import get_azure_ad_credentials

# Get Azure AD credentials from Key Vault
try:
    ad_credentials = get_azure_ad_credentials()
    CLIENT_ID = ad_credentials["client_id"]
    CLIENT_SECRET = ad_credentials["client_secret"]
    TENANT_ID = ad_credentials["tenant_id"]
except Exception as e:
    st.error(f"Failed to retrieve Azure AD credentials: {e}")
    st.stop()

# Azure AD Configuration
AUTH_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize"
TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
SCOPE = "https://graph.microsoft.com/User.Read"
REDIRECT_URI = "http://localhost:8501/callback" # Changed from /callback to / for simpler query param handling

def get_auth_url():
    """
    Generate Azure AD authorization URL
    """
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "response_mode": "query",
        "scope": SCOPE,
        "state": "demo_state"  # In production, use a random state
    }
    
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{AUTH_URL}?{query_string}"

def exchange_code_for_token(code):
    """
    Exchange authorization code for access token
    """
    try:
        payload = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPE
        }
        
        response = requests.post(TOKEN_URL, data=payload)
        
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            st.error(f"Token exchange failed: {response.text}")
            return None
            
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return None

def authenticate_user_demo():
    """
    Demo authentication for development purposes
    """
    # For demo purposes, return a demo token
    # In production, this would handle the full OAuth flow
    return "demo-token"

def check_authentication():
    """
    Check if user is authenticated
    """
    if "access_token" not in st.session_state or st.session_state["access_token"] is None:
        return False
    return True

def logout():
    """
    Clear authentication state
    """
    if "access_token" in st.session_state:
        del st.session_state["access_token"]
    if "user_info" in st.session_state:
        del st.session_state["user_info"]

def get_user_profile(access_token):
    """
    Fetch the user's profile from Microsoft Graph API using the access token
    """
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch user profile: {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        st.error(f"Error fetching user profile: {e}")
        return {}
