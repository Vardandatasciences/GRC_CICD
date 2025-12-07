# Microsoft Sentinel OAuth Error: AADSTS90102

## Error Message
```
AADSTS90102: 'redirect_uri' value must be a valid absolute URI.
```

## Root Causes

### 1. **Environment Variable Name Mismatch**
- **Code expects**: `REDIRECT_URI` (line 67 in `sentinel.py`)
- **Settings.py uses**: `MICROSOFT_REDIRECT_URI` (line 453 in `settings.py`)
- **Result**: Code gets empty string because variable doesn't exist

### 2. **Empty String Default Value**
- When `REDIRECT_URI` is not set, it defaults to `''` (empty string)
- Microsoft OAuth requires a **valid absolute URI** like:
  - ✅ `https://your-domain.com/auth/sentinel/callback`
  - ✅ `http://localhost:8000/auth/sentinel/callback`
  - ❌ `` (empty string)
  - ❌ `/auth/sentinel/callback` (relative URL)

### 3. **Not Using Django Settings**
- Code directly reads from `os.getenv()` instead of using Django's `settings.REDIRECT_URI`
- This causes inconsistency with other parts of the application

## Expected Redirect URI

Based on your URL routing (line 98 in `backend/urls.py`), the callback route is:
- Route: `/auth/sentinel/callback`
- Full URL (production): `https://grc-backend.vardaands.com/auth/sentinel/callback`
- Full URL (local): `http://localhost:8000/auth/sentinel/callback` (or your Django port)

## Solution

### Option 1: Set Environment Variable (Quick Fix)
Set the `REDIRECT_URI` environment variable to match your callback URL:

**For Production:**
```bash
export REDIRECT_URI="https://grc-backend.vardaands.com/auth/sentinel/callback"
```

**For Local Development:**
```bash
export REDIRECT_URI="http://localhost:8000/auth/sentinel/callback"
```

### Option 2: Fix Code to Use Correct Variable Name (Recommended)
Change line 67 in `sentinel.py` to use `MICROSOFT_REDIRECT_URI`:

```python
self.redirect_uri = os.getenv('MICROSOFT_REDIRECT_URI', 'https://grc-backend.vardaands.com/auth/sentinel/callback')
```

### Option 3: Use Django Settings (Best Practice)
Import Django settings and use the configured value:

```python
from django.conf import settings
# ...
self.redirect_uri = getattr(settings, 'REDIRECT_URI', 'https://grc-backend.vardaands.com/auth/sentinel/callback')
```

## Important: Azure AD Configuration

Make sure your redirect URI is **exactly** registered in Azure AD:

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Select your app (Client ID: `1d9fdf2e-ebc8-47e0-8e7d-4c4c41b6a616`)
4. Go to **Authentication** → **Redirect URIs**
5. Add your redirect URI:
   - Production: `https://grc-backend.vardaands.com/auth/sentinel/callback`
   - Local (optional): `http://localhost:8000/auth/sentinel/callback`

**⚠️ Important**: The redirect URI in your code MUST match exactly (including protocol, domain, port, and path) with what's registered in Azure AD.

## Verification Steps

1. Check environment variable is set:
   ```bash
   echo $REDIRECT_URI
   ```

2. Check Azure AD redirect URI configuration matches

3. Check code is using the correct value by adding debug logging:
   ```python
   print(f"[SENTINEL] Redirect URI: {self.redirect_uri}")
   ```

4. Ensure the redirect URI is a valid absolute URL (starts with `http://` or `https://`)

