#!/usr/bin/env python3
"""
BambooHR OAuth Flask Server
Integrates with Django backend for BambooHR OAuth flow
Based on the original test.py but modified for production integration
"""

import os
import secrets
import urllib.parse as up
import requests
from flask import Flask, redirect, request, session, url_for, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))

# BambooHR OAuth Configuration
CLIENT_ID = os.environ.get("BAMBOOHR_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("BAMBOOHR_CLIENT_SECRET", "").strip()

# Get environment configuration
USE_LOCAL = os.environ.get("USE_LOCAL_DEVELOPMENT", "True").lower() == "true"

# Set URLs based on environment
if USE_LOCAL:
    REDIRECT_URI = "http://127.0.0.1:8000/api/bamboohr/oauth-callback/"
    DJANGO_BACKEND_URL = os.environ.get("DJANGO_BACKEND_URL", "http://127.0.0.1:8000")
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:8080")
    print("🌍 Running in LOCAL development mode")
else:
    REDIRECT_URI = "https://grc-backend.vardaands.com/api/bamboohr/oauth-callback/"
    DJANGO_BACKEND_URL = os.environ.get("DJANGO_BACKEND_URL", "https://grc-backend.vardaands.com")
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:8080")
    print("🌍 Running in PRODUCTION mode")

REDIRECT_URI = os.environ.get("BAMBOOHR_REDIRECT_URI", REDIRECT_URI).strip()
SCOPES = os.environ.get("BAMBOOHR_SCOPES", "email openid employee company:info employee:contact employee:job employee:name employee:photo employee_directory").split()

def form_headers():
    return {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}

def auth_headers(access_token):
    return {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

@app.route("/")
def home():
    return """
    <h3>BambooHR OAuth Integration Server</h3>
    <p>This server handles BambooHR OAuth flow for the GRC application.</p>
    <p><strong>Status:</strong> Running</p>
    <hr>
    <p><a href="/health">Health Check</a></p>
    """

@app.route("/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "BambooHR OAuth Server",
        "version": "1.0.0"
    })

@app.route("/set-subdomain-and-login")
def set_subdomain_and_login():
    """Handle subdomain setting and initiate OAuth flow"""
    subdomain = request.args.get("subdomain", "").strip()
    user_id = request.args.get("user_id", "1")
    
    if not subdomain:
        return redirect(f"{FRONTEND_URL}/integration/bamboohr?error=missing_subdomain")
    
    if not CLIENT_ID or not CLIENT_SECRET:
        return redirect(f"{FRONTEND_URL}/integration/bamboohr?error=oauth_not_configured")
    
    # Store subdomain and user_id in session
    session["subdomain"] = subdomain
    session["user_id"] = user_id
    
    # Initiate OAuth flow
    return redirect(url_for("login"))

@app.route("/login")
def login():
    """Initiate OAuth flow with BambooHR"""
    # Check if subdomain is set
    if "subdomain" not in session:
        return redirect(f"{FRONTEND_URL}/integration/bamboohr?error=session_expired")
    
    state = secrets.token_urlsafe(24)
    session["oauth_state"] = state
    
    # Use dynamic subdomain from session
    subdomain = session["subdomain"]
    auth_base = f"https://{subdomain}.bamboohr.com/authorize.php"
    
    params = {
        "request": "authorize",
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "state": state,
    }
    
    oauth_url = f"{auth_base}?{up.urlencode(params)}"
    print(f"🔗 Redirecting to BambooHR OAuth: {oauth_url}")
    
    return redirect(oauth_url)

@app.route("/oauth/callback")
def oauth_callback():
    """Handle OAuth callback from BambooHR"""
    try:
        # Verify state parameter
        if request.args.get("state") != session.get("oauth_state"):
            print("❌ OAuth state mismatch")
            return redirect(f"{FRONTEND_URL}/integration/bamboohr?error=state_mismatch")

        code = request.args.get("code")
        if not code:
            error_description = request.args.get("error_description", "Missing authorization code")
            print(f"❌ OAuth error: {error_description}")
            return redirect(f"{FRONTEND_URL}/integration/bamboohr?error={error_description}")

        # Check if subdomain and user_id are in session
        subdomain = session.get("subdomain")
        user_id = session.get("user_id", "1")
        
        if not subdomain:
            return redirect(f"{FRONTEND_URL}/integration/bamboohr?error=session_expired")

        # Exchange code for access token
        token_base = f"https://{subdomain}.bamboohr.com/token.php"
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
        
        print(f"🔄 Exchanging code for token with {subdomain}.bamboohr.com")
        token_resp = requests.post(f"{token_base}?request=token", headers=form_headers(), data=data, timeout=30)
        
        if token_resp.status_code != 200:
            print(f"❌ Token exchange failed: {token_resp.status_code} {token_resp.text}")
            return redirect(f"{FRONTEND_URL}/integration/bamboohr?error=token_exchange_failed")

        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            print("❌ No access token in response")
            return redirect(f"{FRONTEND_URL}/integration/bamboohr?error=no_access_token")

        print(f"✅ Access token received: {access_token[:20]}...")
        
        # Store access token in session
        session["access_token"] = access_token
        
        # Test the token by fetching basic data
        api_base = f"https://{subdomain}.bamboohr.com/api/v1"
        headers = auth_headers(access_token)
        
        # Try to fetch company info to verify token works
        try:
            company_resp = requests.get(f"{api_base}/meta/company", headers=headers, timeout=30)
            if company_resp.status_code == 200:
                company_info = company_resp.json()
                print(f"✅ Token verified with company: {company_info}")
            else:
                print(f"⚠️ Could not verify token with company API: {company_resp.status_code}")
        except Exception as e:
            print(f"⚠️ Error verifying token: {e}")
        
        # Notify Django backend about successful connection
        try:
            callback_url = f"{DJANGO_BACKEND_URL}/api/bamboohr/oauth-callback/"
            callback_data = {
                "access_token": access_token,
                "user_id": user_id,
                "subdomain": subdomain,
                "account_info": {
                    "account_id": f"bamboohr_{subdomain}_{user_id}",
                    "account_type": "bamboohr",
                    "name": f"{subdomain}.bamboohr.com"
                }
            }
            
            print(f"📡 Notifying Django backend: {callback_url}")
            django_resp = requests.post(callback_url, json=callback_data, timeout=30)
            
            if django_resp.status_code == 200:
                print("✅ Django backend notified successfully")
            else:
                print(f"⚠️ Django backend notification failed: {django_resp.status_code}")
        
        except Exception as e:
            print(f"⚠️ Error notifying Django backend: {e}")
        
        # Redirect back to frontend with success
        frontend_callback_url = f"{FRONTEND_URL}/integration/bamboohr?token={access_token}&user_id={user_id}&subdomain={subdomain}&success=true"
        print(f"🔗 Redirecting to frontend: {frontend_callback_url}")
        
        # Clear sensitive session data
        session.pop("oauth_state", None)
        session.pop("access_token", None)
        
        return redirect(frontend_callback_url)
        
    except Exception as e:
        print(f"❌ OAuth callback error: {str(e)}")
        return redirect(f"{FRONTEND_URL}/integration/bamboohr?error=callback_error")

@app.route("/test-connection")
def test_connection():
    """Test endpoint to verify server is running"""
    return jsonify({
        "status": "ok",
        "message": "BambooHR OAuth server is running",
        "endpoints": {
            "health": "/health",
            "oauth_initiate": "/set-subdomain-and-login",
            "oauth_callback": "/oauth/callback"
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Not Found",
        "message": "The requested endpoint was not found",
        "available_endpoints": ["/", "/health", "/test-connection"]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal Server Error",
        "message": "An internal server error occurred"
    }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    
    print(f"🚀 Starting BambooHR OAuth Server on port {port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"🌍 Environment: {'LOCAL' if USE_LOCAL else 'PRODUCTION'}")
    print(f"🌐 Django Backend: {DJANGO_BACKEND_URL}")
    print(f"🌐 Frontend URL: {FRONTEND_URL}")
    print(f"🔗 Redirect URI: {REDIRECT_URI}")
    print(f"🔑 Client ID configured: {'Yes' if CLIENT_ID else 'No'}")
    print(f"🔐 Client Secret configured: {'Yes' if CLIENT_SECRET else 'No'}")
    
    app.run(host="0.0.0.0", port=port, debug=debug)