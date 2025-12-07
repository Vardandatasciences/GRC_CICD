# BambooHR OAuth Environment Setup

## Required Environment Variables

Add these environment variables to your Django settings or `.env` file:

```bash
# BambooHR OAuth Configuration
BAMBOOHR_CLIENT_ID=your_bamboohr_client_id_here
BAMBOOHR_CLIENT_SECRET=your_bamboohr_client_secret_here
BAMBOOHR_REDIRECT_URI=http://127.0.0.1:8000/oauth/callback
BAMBOOHR_SCOPES=email openid employee company:info employee:contact employee:job employee:name employee:photo employee_directory

# Frontend URL (for redirects)
FRONTEND_URL=http://localhost:8080
```

## BambooHR App Configuration

1. Log into your BambooHR account as an admin
2. Go to **Settings > API Keys**
3. Create a new OAuth application with these settings:
   - **Redirect URI**: `http://127.0.0.1:8000/oauth/callback`
   - **Scopes**: Select all the permissions listed in BAMBOOHR_SCOPES above
4. Copy the **Client ID** and **Client Secret** to your environment variables

## How It Works

1. User enters their BambooHR subdomain (e.g., "acme" for acme.bamboohr.com)
2. Frontend calls Django OAuth endpoint: `/api/bamboohr/oauth/?user_id=1&subdomain=acme`
3. Django redirects to BambooHR: `https://acme.bamboohr.com/authorize.php?...`
4. User authenticates with BambooHR
5. BambooHR redirects back to: `http://127.0.0.1:8000/oauth/callback?code=...&state=...`
6. Django exchanges code for access token
7. Django saves connection to database
8. Django redirects back to frontend with success/error status

## Testing

1. Make sure your Django backend is running on `http://127.0.0.1:8000`
2. Make sure your frontend is running on `http://localhost:8080`
3. Go to External Integrations page
4. Click "Connect" on BambooHR
5. Enter your BambooHR subdomain
6. Click "Connect to BambooHR"
7. Complete OAuth flow

## Troubleshooting

- **"OAuth not configured"**: Make sure BAMBOOHR_CLIENT_ID and BAMBOOHR_CLIENT_SECRET are set
- **"State mismatch"**: Session expired, try again
- **"Token exchange failed"**: Check your BambooHR app configuration and credentials
- **"No access token"**: BambooHR didn't return a token, check scopes and app settings
