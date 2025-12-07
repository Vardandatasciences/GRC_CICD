# BambooHR Integration Setup

This directory contains the BambooHR OAuth integration for the GRC application.

## Files

- `bamboohr.py` - Django backend endpoints for BambooHR integration
- `flask_oauth_server.py` - Flask OAuth server for handling BambooHR OAuth flow
- `test.py` - Original test file (reference only)

## Setup Instructions

### 1. BambooHR App Configuration

1. Log into your BambooHR account as an admin
2. Go to Settings > API Keys
3. Create a new OAuth application with these settings:
   - **Redirect URI**: `http://localhost:5000/oauth/callback`
   - **Scopes**: Select the following permissions:
     - Email
     - OpenID
     - Employee
     - Company Info
     - Employee Contact
     - Employee Job
     - Employee Name
     - Employee Photo
     - Employee Directory

4. Note down your **Client ID** and **Client Secret**

### 2. Environment Configuration

Create a `.env` file in this directory with:

```bash
# Flask Configuration
FLASK_SECRET_KEY=your_generated_secret_key_here
FLASK_DEBUG=False
PORT=5000

# BambooHR OAuth Credentials
BAMBOOHR_CLIENT_ID=your_bamboohr_client_id
BAMBOOHR_CLIENT_SECRET=your_bamboohr_client_secret
BAMBOOHR_REDIRECT_URI=http://localhost:5000/oauth/callback
BAMBOOHR_SCOPES=email openid employee company:info employee:contact employee:job employee:name employee:photo employee_directory

# Integration URLs
DJANGO_BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
BAMBOOHR_FLASK_URL=http://localhost:5000
```

### 3. Install Dependencies

```bash
pip install flask python-dotenv requests
```

### 4. Start the Flask OAuth Server

```bash
cd backend/grc/routes/Integrations/Bamboohr/
python flask_oauth_server.py
```

The server will start on `http://localhost:5000`

### 5. Start Your Django Backend

Make sure your Django backend is running on `http://localhost:8000`

### 6. Start Your Frontend

Make sure your frontend is running on `http://localhost:3000`

## Usage Flow

1. User goes to External Integrations page
2. Clicks "Connect" on BambooHR platform
3. New popup window opens with BambooHR integration page
4. User enters their BambooHR subdomain (e.g., "acme" for acme.bamboohr.com)
5. User clicks "Connect to BambooHR"
6. Redirected to Flask OAuth server
7. Flask server redirects to BambooHR for authentication
8. After successful authentication, BambooHR redirects back to Flask server
9. Flask server processes the OAuth callback and notifies Django backend
10. User is redirected back to frontend with success/error status
11. Popup window closes and main window updates connection status

## API Endpoints

### Django Backend Endpoints

- `GET /api/bamboohr/oauth/` - Initiate OAuth flow
- `GET/POST /api/bamboohr/oauth-callback/` - Handle OAuth callback
- `GET/POST /api/bamboohr/employees/` - Get employee data
- `GET /api/bamboohr/stored-data/` - Get stored data
- `POST /api/bamboohr/sync-data/` - Sync employee data

### Flask OAuth Server Endpoints

- `GET /` - Server status page
- `GET /health` - Health check
- `GET /set-subdomain-and-login` - Initiate OAuth with subdomain
- `GET /login` - Start OAuth flow
- `GET /oauth/callback` - Handle OAuth callback from BambooHR

## Troubleshooting

### Common Issues

1. **"OAuth not configured" error**
   - Make sure `BAMBOOHR_CLIENT_ID` and `BAMBOOHR_CLIENT_SECRET` are set in your `.env` file

2. **"State mismatch" error**
   - This usually happens if the Flask server restarts during OAuth flow
   - Try the connection process again

3. **"Token exchange failed" error**
   - Check that your BambooHR app configuration matches your environment variables
   - Verify the redirect URI is exactly `http://localhost:5000/oauth/callback`

4. **Popup blocked**
   - Make sure your browser allows popups for the frontend domain
   - Some browsers block popups by default

### Debug Mode

To enable debug mode, set `FLASK_DEBUG=True` in your `.env` file. This will show detailed error messages and stack traces.

## Security Notes

- The Flask OAuth server should only be used for development/testing
- In production, implement proper OAuth flow within your Django application
- Never commit your `.env` file with real credentials to version control
- Use HTTPS in production environments
