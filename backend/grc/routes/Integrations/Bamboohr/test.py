import os
import secrets
import urllib.parse as up

from flask import Flask, redirect, request, session, url_for, jsonify
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))

SUBDOMAIN     = os.environ["BAMBOOHR_SUBDOMAIN"].strip()
CLIENT_ID     = os.environ["BAMBOOHR_CLIENT_ID"].strip()
CLIENT_SECRET = os.environ["BAMBOOHR_CLIENT_SECRET"].strip()
REDIRECT_URI  = os.environ["BAMBOOHR_REDIRECT_URI"].strip()
SCOPES        = os.environ.get("BAMBOOHR_SCOPES", "email openid employee company:info employee:contact employee:job employee:name employee:photo employee_directory").split()

AUTH_BASE  = f"https://{SUBDOMAIN}.bamboohr.com/authorize.php"
TOKEN_BASE = f"https://{SUBDOMAIN}.bamboohr.com/token.php"
API_BASE   = f"https://{SUBDOMAIN}.bamboohr.com/api/v1"

def form_headers():
    return {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}

def auth_headers():
    return {"Authorization": f"Bearer {session.get('access_token')}", "Accept": "application/json"}

@app.route("/")
def home():
    return (
        "<h3>BambooHR OAuth Demo</h3>"
        "<p>Enter your BambooHR subdomain to get started:</p>"
        "<form method='post' action='/set-subdomain'>"
        "<input type='text' name='subdomain' placeholder='your-company' required>"
        "<span>.bamboohr.com</span><br><br>"
        "<button type='submit'>Continue to Login</button>"
        "</form>"
        "<hr>"
        "<ul>"
        "<li><a href='/me'>Fetch logged-in user (or company info)</a></li>"
        "<li><a href='/logout'>Logout</a></li>"
        "</ul>"
    )

@app.route("/set-subdomain", methods=["POST"])
def set_subdomain():
    subdomain = request.form.get("subdomain", "").strip()
    if not subdomain:
        return "Subdomain is required", 400
    
    # Store subdomain in session
    session["subdomain"] = subdomain
    return redirect(url_for("login"))

@app.route("/login")
def login():
    # Check if subdomain is set
    if "subdomain" not in session:
        return redirect(url_for("home"))
    
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
    return redirect(f"{auth_base}?{up.urlencode(params)}")

@app.route("/oauth/callback")
def oauth_callback():
    if request.args.get("state") != session.get("oauth_state"):
        return "State mismatch", 400

    code = request.args.get("code")
    if not code:
        return "Missing ?code", 400

    # Check if subdomain is set
    if "subdomain" not in session:
        return "Subdomain not set", 400

    # Use dynamic subdomain from session
    subdomain = session["subdomain"]
    token_base = f"https://{subdomain}.bamboohr.com/token.php"

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    token_resp = requests.post(f"{token_base}?request=token", headers=form_headers(), data=data, timeout=30)
    if token_resp.status_code != 200:
        return f"Token exchange failed: {token_resp.status_code} {token_resp.text}", 400

    tok = token_resp.json()
    session["access_token"] = tok.get("access_token")
    return redirect(url_for("me"))

@app.route("/me")
def me():
    if "access_token" not in session:
        return redirect(url_for("login"))
    
    if "subdomain" not in session:
        return redirect(url_for("home"))

    # Use dynamic subdomain from session
    subdomain = session["subdomain"]
    api_base = f"https://{subdomain}.bamboohr.com/api/v1"
    
    headers = auth_headers()
    data_collected = {}
    access_token = session.get('access_token', 'None')[:20]

    # Step 1: Try to get logged-in user from /meta/users
    try:
        users_resp = requests.get(f"{api_base}/meta/users", headers=headers, timeout=30)
        print(f"Users API response: {users_resp.status_code}")
        
        if users_resp.status_code == 200:
            users = users_resp.json().get("users", [])
            print(f"Found {len(users)} users")
            data_collected["users_info"] = users_resp.json()
            current_user = next((u for u in users if u.get("self")), None)

            if current_user:
                employee_id = current_user["employeeId"]
                print(f"Current user employee ID: {employee_id}")
                fields = [
                    "id","displayName","firstName","lastName","jobTitle","department",
                    "division","location","workEmail","mobilePhone","workPhone","hireDate",
                    "supervisor","supervisorId","status"
                ]
                emp_resp = requests.get(
                    f"{api_base}/employees/{employee_id}",
                    params={"fields": ",".join(fields)},
                    headers=headers,
                    timeout=30
                )
                print(f"Employee API response: {emp_resp.status_code}")
                if emp_resp.status_code == 200:
                    profile = emp_resp.json()
                    data_collected["current_user_profile"] = profile
                    print("=== Logged-in User Profile ===")
                    print(profile)
                else:
                    print(f"Employee API error: {emp_resp.text}")
        elif users_resp.status_code == 401:
            print(f"Users API error: {users_resp.status_code} - Unauthorized")
        else:
            print(f"Users API error: {users_resp.text}")
    except Exception as e:
        print(f"Exception in users API call: {e}")

    # Step 2: Try to get company information
    try:
        company_resp = requests.get(f"{api_base}/meta/company", headers=headers, timeout=30)
        print(f"Company API response: {company_resp.status_code}")
        if company_resp.status_code == 200:
            data_collected["company_info"] = company_resp.json()
            print("✓ Company info retrieved")
        else:
            print(f"Company API error: {company_resp.status_code}")
    except Exception as e:
        print(f"Exception in company API call: {e}")

    # Step 3: Try to get employee directory
    try:
        directory_resp = requests.get(f"{api_base}/employees/directory", headers=headers, timeout=30)
        print(f"Directory API response: {directory_resp.status_code}")
        if directory_resp.status_code == 200:
            data_collected["employee_directory"] = directory_resp.json()
            print("✓ Employee directory retrieved")
        else:
            print(f"Directory API error: {directory_resp.status_code}")
    except Exception as e:
        print(f"Exception in directory API call: {e}")

    # Step 4: Try to get reports list
    try:
        reports_resp = requests.get(f"{api_base}/reports", headers=headers, timeout=30)
        print(f"Reports API response: {reports_resp.status_code}")
        if reports_resp.status_code == 200:
            data_collected["reports"] = reports_resp.json()
            print("✓ Reports retrieved")
        else:
            print(f"Reports API error: {reports_resp.status_code}")
    except Exception as e:
        print(f"Exception in reports API call: {e}")

    # If we got any data, display it
    if data_collected:
        return f"""
        <h2>BambooHR Data Retrieved Successfully!</h2>
        <h3>Company: {subdomain}.bamboohr.com</h3>
        <h3>Access Token: {access_token}...</h3>
        <hr>
        <h3>Available Data:</h3>
        <ul>
        {''.join([f'<li><strong>{key.replace("_", " ").title()}:</strong> Retrieved ✓</li>' for key in data_collected.keys()])}
        </ul>
        <hr>
        <h3>Raw Data:</h3>
        <pre>{jsonify(data_collected).get_data(as_text=True)}</pre>
        <hr>
        <p><a href="/">← Back to Home</a> | <a href="/logout">Logout</a></p>
        """
    else:
        # If no data was retrieved, show error and redirect
        return f"""
        <h2>No Data Retrieved</h2>
        <p>Company: {subdomain}.bamboohr.com</p>
        <p>The access token may not have sufficient permissions for any of the available endpoints.</p>
        <p>Access Token: {access_token}...</p>
        <p>Try logging in again or check your BambooHR app permissions.</p>
        <p><a href="/">← Back to Home</a> | <a href="/logout">Logout</a></p>
        """

@app.route("/logout")
def logout():
    session.clear()
    return "Logged out."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
