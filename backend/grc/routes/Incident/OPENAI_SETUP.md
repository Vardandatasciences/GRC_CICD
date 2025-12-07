# OpenAI Setup Guide for Incident AI Import

## Overview
The Incident AI Import module now uses OpenAI's GPT models instead of Ollama for incident data extraction from documents.

## Prerequisites

### 1. Install OpenAI Library
```bash
pip install openai
```

### 2. Get OpenAI API Key
1. Go to https://platform.openai.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (you won't be able to see it again!)

## Environment Configuration

### Set Environment Variables

#### Option 1: Using .env file (Recommended)
Create or update your `.env` file in the project root:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_API_BASE=https://api.openai.com/v1
```

#### Option 2: System Environment Variables

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="sk-your-api-key-here"
$env:OPENAI_MODEL="gpt-3.5-turbo"
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
export OPENAI_MODEL="gpt-3.5-turbo"
```

## Available Models

### GPT-3.5 Models (Faster & Cheaper)
- `gpt-3.5-turbo` - Most cost-effective, good for most tasks
- `gpt-3.5-turbo-16k` - Larger context window

### GPT-4 Models (More Accurate)
- `gpt-4` - Best quality, slower and more expensive
- `gpt-4-turbo` - Faster GPT-4 variant
- `gpt-4-32k` - Largest context window

**Recommendation:** Start with `gpt-3.5-turbo` for testing, upgrade to `gpt-4` if you need better accuracy.

## Cost Estimation

### GPT-3.5-turbo Pricing (as of 2024)
- Input: ~$0.0005 per 1K tokens
- Output: ~$0.0015 per 1K tokens

### Typical Document Processing Cost
- Small document (1-2 pages): ~$0.01 - $0.03
- Medium document (5-10 pages): ~$0.05 - $0.10
- Large document (20+ pages): ~$0.15 - $0.30

## Testing the Setup

### 1. Check API Connection
```bash
curl http://localhost:8000/api/ai-incident-test/
```

Expected response:
```json
{
    "status": "success",
    "openai_reply": {"ok": true},
    "model": "gpt-3.5-turbo",
    "api_base": "https://api.openai.com/v1",
    "module": "incident",
    "api_provider": "OpenAI"
}
```

### 2. Test Document Upload
Use the frontend interface or API:
```bash
POST /api/ai-incident-upload/
Content-Type: multipart/form-data

file: <your-document.pdf>
user_id: 1
```

## Troubleshooting

### Error: "OPENAI_API_KEY not set"
**Solution:** Set the environment variable as shown above.

### Error: "Rate limit exceeded"
**Solution:** 
- Wait a few minutes before retrying
- Upgrade your OpenAI plan for higher rate limits
- The system automatically retries with exponential backoff

### Error: "Invalid API key"
**Solution:**
- Check that your API key is correct
- Ensure there are no extra spaces or quotes
- Verify the key is active in your OpenAI dashboard

### Error: "Insufficient credits"
**Solution:**
- Add credits to your OpenAI account
- Check your usage at https://platform.openai.com/usage

## Security Best Practices

1. **Never commit API keys to version control**
   - Add `.env` to `.gitignore`
   - Use environment variables only

2. **Rotate keys regularly**
   - Generate new keys every 3-6 months
   - Delete old keys from OpenAI dashboard

3. **Set spending limits**
   - Configure usage limits in OpenAI dashboard
   - Monitor usage regularly

4. **Use separate keys for dev/prod**
   - Different keys for testing and production
   - Easier to track usage and rotate

## Features Preserved

All existing functionality remains the same:
- ✅ Document upload (PDF, DOCX, XLSX, TXT)
- ✅ AI-powered field extraction
- ✅ Missing field prediction
- ✅ Confidence scoring
- ✅ Metadata tracking
- ✅ Review interface
- ✅ Database saving

## Support

For OpenAI-specific issues:
- OpenAI Documentation: https://platform.openai.com/docs
- OpenAI Status: https://status.openai.com/
- OpenAI Community: https://community.openai.com/

For application issues:
- Check the Django logs
- Review the browser console for frontend errors
- Verify environment variables are set correctly

