# Risk AI Document Ingestion Feature

## Overview
This feature allows users to upload documents (PDF, DOCX, Excel) containing risk data. The system uses Ollama LLM to extract and generate risk information, then saves it to the database.

## Features
- **Multi-format Support**: Upload PDF, DOCX, or Excel files
- **AI-Powered Extraction**: Automatically extracts risk data from documents
- **Intelligent Generation**: Uses Ollama LLM to generate missing fields
- **Interactive Review**: Review and edit extracted data before saving
- **Batch Processing**: Process multiple risks from a single document

## Architecture

### Frontend Components
1. **risk_ai.vue** - Main upload and review interface
   - File upload form
   - Processing indicator with progress bar
   - Risk data review form
   - Success confirmation

2. **risk_ai.css** - Styling for the component
   - Modern, gradient-based design
   - Responsive layout
   - Smooth animations

3. **Sidebar.vue** - Navigation menu
   - New "AI Document Ingestion" menu item under Risk module

### Backend Components
1. **risk_ai_doc.py** - Main processing logic
   - Document text extraction (PDF, DOCX, Excel)
   - Ollama API integration
   - Risk data parsing and generation
   - Database operations

2. **URLs Configuration**
   - `/api/risk/ai/upload-document/` - Upload and process document
   - `/api/risk/ai/save-risks/` - Save extracted risks to database
   - `/api/risk/ai/test-ollama/` - Test Ollama connection

## Setup Instructions

### 1. Install Ollama
```bash
# Install Ollama (visit https://ollama.ai for platform-specific instructions)
# For Linux:
curl https://ollama.ai/install.sh | sh

# For Windows: Download from https://ollama.ai/download
```

### 2. Pull an LLM Model
```bash
# Pull Llama 2 (recommended)
ollama pull llama2

# Or use Mistral for better performance
ollama pull mistral

# Or use Mixtral for advanced use cases
ollama pull mixtral
```

### 3. Configure Environment Variables
Add these to your environment or `.env` file:

```bash
# Ollama Configuration
OLLAMA_API_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama2  # or mistral, mixtral, etc.
```

### 4. Start Ollama Service
```bash
# Start Ollama server
ollama serve

# The API will be available at http://localhost:11434
```

### 5. Verify Installation
Test the Ollama connection:
```bash
# From your Django project root
python manage.py shell

>>> from grc.routes.Risk.risk_ai_doc import test_ollama_connection
>>> from django.http import HttpRequest
>>> request = HttpRequest()
>>> result = test_ollama_connection(request)
>>> print(result.content)
```

Or use the API endpoint:
```bash
curl http://localhost:8000/api/risk/ai/test-ollama/
```

## Usage Guide

### 1. Navigate to Risk AI Document Upload
- Open the GRC application
- Go to **Risk** → **AI Document Ingestion**

### 2. Upload Document
- Click "Choose File" or drag and drop a document
- Supported formats: PDF, DOCX, XLSX, XLS
- Click "Process with AI"

### 3. Review Extracted Risks
- The system will extract text from the document
- Ollama LLM analyzes the text and identifies risks
- Review each risk in the form
- Edit any fields as needed
- Remove unwanted risks using the trash icon

### 4. Save to Database
- Click "Save All Risks"
- Risks are saved to the `risk` table
- Navigate to Risk Register to view saved risks

## Document Format Guidelines

### Best Practices for Document Content
To get the best results, structure your documents with:

1. **Clear Risk Titles**: Each risk should have a clear heading
2. **Structured Information**: Use sections like:
   - Risk Description
   - Category
   - Impact
   - Likelihood
   - Mitigation

3. **Tabular Data**: Excel files should have columns matching risk fields:
   ```
   | Risk Title | Category | Description | Impact | Likelihood | Mitigation |
   |------------|----------|-------------|--------|------------|------------|
   ```

### Example Document Structure (PDF/DOCX)
```
Risk 1: Data Breach Risk
Category: Cybersecurity
Description: Potential unauthorized access to customer data
Impact: High
Likelihood: Medium
Mitigation: Implement encryption and access controls

Risk 2: Market Risk
Category: Financial
Description: Exposure to market volatility
Impact: High
Likelihood: High
Mitigation: Diversify investment portfolio
```

## API Reference

### Upload and Process Document
**Endpoint**: `POST /api/risk/ai/upload-document/`

**Request**:
```javascript
FormData {
  file: <File>,
  user_id: <string>
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Successfully extracted 5 risk(s)",
  "risks": [
    {
      "RiskTitle": "Data Breach Risk",
      "RiskDescription": "...",
      "Category": "Cybersecurity",
      "Criticality": "High",
      "RiskPriority": "High",
      "RiskType": "Current",
      "BusinessImpact": "...",
      "PossibleDamage": "...",
      "RiskMitigation": "...",
      "RiskLikelihood": 7,
      "RiskImpact": 8,
      "RiskExposureRating": 56,
      "ai_generated_fields": ["Criticality", "RiskPriority"]
    }
  ],
  "document_name": "risks.pdf",
  "extracted_text_length": 5000
}
```

### Save Extracted Risks
**Endpoint**: `POST /api/risk/ai/save-risks/`

**Request**:
```json
{
  "risks": [
    {
      "RiskTitle": "Data Breach Risk",
      "RiskDescription": "...",
      "Category": "Cybersecurity",
      ...
    }
  ],
  "user_id": "1"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Successfully saved 5 risk(s)",
  "saved_count": 5,
  "saved_risks": [
    {
      "risk_id": 101,
      "risk_title": "Data Breach Risk"
    }
  ]
}
```

## Database Schema

The extracted risks are saved to the `risk` table with these fields:

| Field | Type | Description |
|-------|------|-------------|
| RiskId | Integer (PK) | Auto-generated ID |
| RiskTitle | Text | Risk title/name |
| RiskDescription | Text | Detailed description |
| Category | String | Risk category |
| Criticality | String | Low/Medium/High/Critical |
| PossibleDamage | Text | Potential damage |
| RiskType | Text | Type of risk |
| BusinessImpact | Text | Business impact description |
| RiskPriority | String | Priority level |
| RiskMitigation | Text | Mitigation strategies |
| RiskLikelihood | Integer | Likelihood score (1-10) |
| RiskImpact | Integer | Impact score (1-10) |
| RiskExposureRating | Float | Calculated exposure rating |
| ComplianceId | Integer (FK) | Optional compliance link |

## Troubleshooting

### Ollama Connection Issues
**Problem**: "Ollama connection failed"

**Solutions**:
1. Ensure Ollama is running: `ollama serve`
2. Check the API URL: `http://localhost:11434/api/generate`
3. Verify the model is downloaded: `ollama list`
4. Check firewall settings

### Document Processing Errors
**Problem**: "Could not extract meaningful text from document"

**Solutions**:
1. Ensure document is not password-protected
2. Check document is not corrupted
3. Try converting to a different format
4. Ensure document contains actual text (not just images)

### No Risks Detected
**Problem**: "No risks could be identified in the document"

**Solutions**:
1. Ensure document contains risk-related content
2. Use clear risk indicators (keywords like "risk", "threat", "vulnerability")
3. Structure data clearly with headers and sections
4. Try a different LLM model (mistral, mixtral)

### Slow Processing
**Problem**: Processing takes too long

**Solutions**:
1. Use a smaller, faster model (llama2 instead of mixtral)
2. Reduce document size/complexity
3. Increase timeout values in `risk_ai_doc.py`
4. Use a GPU-accelerated Ollama setup

## Performance Optimization

### For Better Accuracy
1. Use larger models: `ollama pull mixtral`
2. Provide more context in documents
3. Use structured formats (Excel with clear columns)

### For Better Speed
1. Use smaller models: `ollama pull llama2`
2. Reduce document length
3. Use GPU acceleration
4. Cache common risk patterns

## Future Enhancements
- [ ] Support for more document formats (CSV, JSON)
- [ ] Batch upload multiple files
- [ ] Custom field mapping
- [ ] Risk deduplication
- [ ] Integration with existing risk framework
- [ ] Scheduled document processing
- [ ] Multi-language support
- [ ] Custom LLM prompts configuration

## Support
For issues or questions:
1. Check the troubleshooting section
2. Review Ollama documentation: https://ollama.ai/docs
3. Test with the `/api/risk/ai/test-ollama/` endpoint
4. Check backend logs for detailed error messages

## License
This feature is part of the GRC platform and follows the same license terms.

