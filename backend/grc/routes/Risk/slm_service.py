import json
import re
import random
import traceback
import os
from openai import OpenAI
from django.conf import settings

class OpenAIIntegration:
    """OpenAI integration class for risk analysis"""
    
    def __init__(self, api_key=None):
        """Initialize OpenAI client with API key from Django settings or parameter"""
        if api_key is None:
            # Try to get from Django settings (which loads from .env file)
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
        
        if not api_key or api_key == 'your-openai-api-key-here' or api_key.startswith('YOUR_OPE'):
            print("⚠️ OpenAI API key not configured properly")
            print("   Please set OPENAI_API_KEY in your .env file")
            self.client = None
            self.is_available = False
        else:
            try:
                self.client = OpenAI(api_key=api_key)
                self.is_available = True
                print("✅ OpenAI client initialized successfully for risk analysis")
                print(f"   Using model: {getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo')}")
            except Exception as e:
                print(f"❌ Failed to initialize OpenAI client: {e}")
                self.client = None
                self.is_available = False
    
    def generate_response(self, prompt, model="gpt-3.5-turbo", max_tokens=2000, temperature=0.3):
        """Send request to OpenAI and get response"""
        if not self.is_available or self.client is None:
            print("OpenAI client is not available")
            return None

        # Clean model name - strip quotes and whitespace
        model_clean = str(model).strip().strip('"').strip("'")
        model_lower = model_clean.lower()
        
        print(f"🔍 Model check - Original: '{model}', Cleaned: '{model_clean}', Lower: '{model_lower}'")
        
        # Models that support json_object response_format:
        # gpt-4-turbo-preview, gpt-4-0125-preview, gpt-3.5-turbo-1106, gpt-4-turbo, gpt-4o
        # Note: gpt-4o-mini does NOT support json_object format
        # Explicitly exclude gpt-4o-mini first (it contains "gpt-4o" but doesn't support json_object)
        if "gpt-4o-mini" in model_lower:
            supports_json_format = False
            print(f"🔍 Model '{model_clean}' is gpt-4o-mini - NOT adding response_format")
        else:
            # Check if model exactly matches or starts with a supported model
            models_with_json_support = [
                "gpt-4-turbo-preview", "gpt-4-0125-preview", "gpt-3.5-turbo-1106", 
                "gpt-4-turbo", "gpt-4o"
            ]
            supports_json_format = any(
                model_lower == supported_model.lower() or model_lower.startswith(supported_model.lower() + "-")
                for supported_model in models_with_json_support
            )
            print(f"🔍 Model '{model_clean}' supports_json_format check result: {supports_json_format}")

        try:
            request_params = {
                "model": model_clean,  # Use cleaned model name
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a senior risk analyst specializing in banking GRC (Governance, Risk, and Compliance) systems. You provide detailed, structured risk assessments in JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # Only add response_format for models that support it
            if supports_json_format:
                request_params["response_format"] = {"type": "json_object"}
                print(f"✅ Adding response_format: json_object (model '{model_clean}' supports it)")
            else:
                print(f"⚠️  NOT adding response_format (model '{model_clean}' does not support json_object)")
            
            print(f"🔍 Request params keys: {list(request_params.keys())}")
            
            response = self.client.chat.completions.create(**request_params)
            
            return response.choices[0].message.content
        except Exception as e:
            error_type = type(e).__name__
            error_message = str(e)
            print(f"❌ OpenAI API error: {error_type}: {error_message}")
            
            # Enhanced error logging for OpenAI SDK exceptions
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_body = e.response.json() if hasattr(e.response, 'json') else {}
                    error_detail = error_body.get('error', {})
                    if isinstance(error_detail, dict):
                        print(f"🔍 OpenAI Error Details:")
                        print(f"   Type: {error_detail.get('type', 'Unknown')}")
                        print(f"   Code: {error_detail.get('code', 'Unknown')}")
                        print(f"   Message: {error_detail.get('message', 'Unknown error')}")
                        print(f"   Full error: {error_detail}")
                except Exception as parse_err:
                    print(f"⚠️  Could not parse error response: {parse_err}")
            print(f"Error calling OpenAI API: {e}")
            traceback.print_exc()
            return None

def analyze_security_incident(incident_description):
    try:
        # Initialize OpenAI integration
        print("🔄 Using OpenAI for risk analysis")
        openai_client = OpenAIIntegration()
        
        if not openai_client.is_available:
            print("⚠️ OpenAI not available, falling back to comprehensive fallback analysis")
            return generate_fallback_analysis(incident_description)

        # Create the comprehensive prompt for banking GRC risk analysis optimized for OpenAI
        prompt = f"""Analyze the following security incident for a banking GRC system and provide a comprehensive risk assessment.

**INCIDENT DETAILS:**
{incident_description}

**REQUIRED JSON STRUCTURE:**
{{
  "criticality": "<Severe/Significant/Moderate/Minor>",
  "possibleDamage": "<detailed potential harm description>",
  "category": "<incident type>",
  "riskDescription": "<cause-effect risk scenario>",
  "riskLikelihood": <integer 1-10>,
  "riskLikelihoodJustification": "<detailed explanation>",
  "riskImpact": <integer 1-10>,
  "riskImpactJustification": "<detailed explanation>",
  "riskExposureRating": "<Critical/High/Elevated/Low Exposure>",
  "riskPriority": "<P0/P1/P2/P3>",
  "riskAppetite": "<Within Appetite/Borderline/Exceeds Appetite>",
  "riskMitigation": ["<step1>", "<step2>", "..."]
}}

**RISK LIKELIHOOD SCALE (1-10):**
- 1-2: Very Unlikely - rare occurrence, multiple safeguards in place
- 3-4: Unlikely - some protective measures, but vulnerabilities exist
- 5-6: Possible - moderate probability, some risk factors present
- 7-8: Likely - high probability, significant risk factors
- 9-10: Almost Certain - imminent threat, critical vulnerabilities exposed

**RISK IMPACT SCALE (1-10):**
- 1-2: Negligible - minimal business disruption, easily recoverable
- 3-4: Minor - limited impact, some operational disruption
- 5-6: Moderate - significant impact, noticeable business disruption
- 7-8: Major - severe impact, substantial financial/operational consequences
- 9-10: Catastrophic - devastating impact, threatens business continuity

**CRITICALITY LEVELS:**
- **Severe**: Threatens core banking operations, payment systems, or customer data security
- **Significant**: Impacts critical systems but doesn't threaten core operations
- **Moderate**: Affects internal systems with limited customer impact
- **Minor**: Minimal operational impact, contained issues

**BANKING CONTEXT:**
- Regulatory frameworks: GLBA, BSA/AML, FFIEC, OCC, FRB, FDIC
- Compliance: SOX, PCI DSS, NYDFS Cybersecurity, Basel III
- Consider: Financial impact, regulatory penalties, reputational damage, customer trust

**ANALYSIS REQUIREMENTS:**
1. **riskLikelihood & riskImpact**: Must be integers between 1-10
2. **Justifications**: Provide detailed explanations considering threat landscape, controls, vulnerabilities, and banking sector specifics
3. **riskMitigation**: Array of specific, actionable steps for banking environments
4. **riskExposureRating**: Calculate based on likelihood × impact matrix
5. **riskPriority**: P0 (critical), P1 (high), P2 (medium), P3 (low)
6. **riskAppetite**: Consider regulatory tolerance, capital requirements, operational risk frameworks

**IMPORTANT:**
- Use banking and GRC terminology throughout
- Provide specific, actionable mitigation steps
- Consider both immediate response and long-term controls
- Response must be ONLY valid JSON, no additional text

Provide comprehensive risk assessment in JSON format."""

        # Process the incident using OpenAI
        print(f"📊 Analyzing risk for incident: {incident_description[:100]}...")
        response = openai_client.generate_response(prompt, model="gpt-3.5-turbo", max_tokens=2000, temperature=0.3)
        
        # Check if response is None (API error)
        if response is None:
            print("❌ OpenAI request failed, falling back to comprehensive fallback analysis")
            return generate_fallback_analysis(incident_description)
       
        # Parse the JSON response with improved error handling
        incident_analysis = parse_ai_response(response)
        
        if incident_analysis:
            print(f"✅ Successfully parsed comprehensive banking GRC risk analysis")
            return incident_analysis
        else:
            print("❌ Failed to parse AI response, falling back to generated analysis")
            return generate_fallback_analysis(incident_description)
            
    except Exception as e:
        print(f"❌ Error with OpenAI processing: {e}")
        traceback.print_exc()
        # Fall back to a generated response if the model fails
        return generate_fallback_analysis(incident_description)

def parse_ai_response(response):
    """
    Parse AI response with robust error handling for different formats.
    Returns parsed JSON object or None if parsing fails.
    """
    try:
        print(f"✅ Received response from OpenAI")
        
        # OpenAI with json_object format should return clean JSON, but let's still clean it
        json_text = response.strip()
        
        # Remove markdown code blocks if present (shouldn't be with json_object format, but just in case)
        if json_text.startswith("```json"):
            json_text = json_text[7:]
        if json_text.startswith("```"):
            json_text = json_text[3:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]
        json_text = json_text.strip()
        
        # Parse JSON
        incident_analysis = json.loads(json_text)
        
        # Validate all required fields are present
        required_fields = [
            'riskLikelihood', 'riskImpact', 'riskLikelihoodJustification', 
            'riskImpactJustification', 'criticality', 'category', 'riskMitigation'
        ]
        missing_fields = [field for field in required_fields if field not in incident_analysis]
        
        if missing_fields:
            print(f"⚠️ Missing required fields in AI response: {missing_fields}")
            return None
        
        # Ensure likelihood and impact are integers between 1-10
        if 'riskLikelihood' in incident_analysis:
            try:
                likelihood = int(incident_analysis['riskLikelihood'])
                incident_analysis['riskLikelihood'] = max(1, min(10, likelihood))
            except (ValueError, TypeError):
                print(f"⚠️ Invalid riskLikelihood value, using default 5")
                incident_analysis['riskLikelihood'] = 5
        
        if 'riskImpact' in incident_analysis:
            try:
                impact = int(incident_analysis['riskImpact'])
                incident_analysis['riskImpact'] = max(1, min(10, impact))
            except (ValueError, TypeError):
                print(f"⚠️ Invalid riskImpact value, using default 5")
                incident_analysis['riskImpact'] = 5
        
        # Ensure list fields are actually lists
        list_fields = ['riskMitigation']
        for field in list_fields:
            if field in incident_analysis:
                if not isinstance(incident_analysis[field], list):
                    # Convert to list if it's a string
                    if isinstance(incident_analysis[field], str):
                        incident_analysis[field] = [incident_analysis[field]]
                    else:
                        print(f"⚠️ Field {field} is not a list, converting to empty list")
                        incident_analysis[field] = []
        
        print(f"✅ Successfully parsed risk analysis with likelihood={incident_analysis['riskLikelihood']}, impact={incident_analysis['riskImpact']}")
        return incident_analysis
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"Response text: {response[:500]}...")  # Print first 500 chars for debugging
        return None
    except Exception as e:
        print(f"❌ Unexpected error during parsing: {e}")
        traceback.print_exc()
        return None

def generate_fallback_analysis(incident_description):
    """Generate a fallback analysis when the AI model is unavailable."""
    # Extract some keywords from the incident for basic categorization
    description_lower = incident_description.lower()
    
    # Default values
    criticality = "Significant"
    category = "IT Security"
    likelihood_score = 5
    impact_score = 5
    priority = "P1"
    
    # Basic categorization based on keywords and assign appropriate scores
    if any(word in description_lower for word in ["breach", "leak", "exposed", "data", "sensitive"]):
        category = "Data Breach"
        criticality = "Severe"
        likelihood_score = 7
        impact_score = 8
        priority = "P0"
        likelihood_justification = "Data breaches have high likelihood due to increasing cyber threats and the valuable nature of banking data. Score of 7 reflects significant threat landscape."
        impact_justification = "Data breaches can cause severe financial losses, regulatory penalties, and reputational damage. Score of 8 reflects major consequences for banking operations."
    elif any(word in description_lower for word in ["malware", "virus", "ransomware", "trojan"]):
        category = "Malware"
        criticality = "Severe"
        likelihood_score = 6
        impact_score = 8
        likelihood_justification = "Malware attacks are moderately likely given current threat environment and banking sector targeting. Score of 6 reflects ongoing risk."
        impact_justification = "Malware can disrupt critical banking systems, encrypt data, and halt operations. Score of 8 reflects severe operational impact."
    elif any(word in description_lower for word in ["phish", "social engineering", "impersonation"]):
        category = "Phishing"
        likelihood_score = 7
        impact_score = 6
        likelihood_justification = "Phishing attacks are highly likely as they target human vulnerabilities and are easy to execute. Score of 7 reflects frequent occurrence."
        impact_justification = "Phishing can lead to credential theft and unauthorized access but impact is more limited. Score of 6 reflects moderate consequences."
    elif any(word in description_lower for word in ["unauthorized", "access", "privilege", "credential"]):
        category = "Unauthorized Access"
        likelihood_score = 6
        impact_score = 7
        likelihood_justification = "Unauthorized access attempts are moderately likely given credential-based attacks. Score of 6 reflects consistent threat level."
        impact_justification = "Unauthorized access can compromise sensitive data and systems integrity. Score of 7 reflects significant potential damage."
    elif any(word in description_lower for word in ["ddos", "denial", "service", "availability"]):
        category = "Denial of Service"
        likelihood_score = 5
        impact_score = 6
        likelihood_justification = "DDoS attacks have moderate likelihood, often used for distraction or service disruption. Score of 5 reflects balanced risk."
        impact_justification = "Service denial can disrupt customer access and operations but recovery is usually possible. Score of 6 reflects moderate impact."
    elif any(word in description_lower for word in ["compliance", "regulatory", "regulation"]):
        category = "Compliance"
        likelihood_score = 4
        impact_score = 7
        likelihood_justification = "Compliance violations have lower likelihood with proper controls but regulatory changes increase risk. Score of 4 reflects controlled environment."
        impact_justification = "Compliance violations can result in significant fines and regulatory sanctions. Score of 7 reflects serious consequences."
    else:
        # Default case
        likelihood_justification = "General security incident with moderate likelihood based on current threat landscape. Score of 5 reflects balanced assessment."
        impact_justification = "Potential impact is moderate considering banking sector criticality and customer data sensitivity. Score of 5 reflects standard risk level."
    
    # Extract a title if possible
    title_match = None
    if "Title:" in incident_description:
        title_parts = incident_description.split("Title:", 1)[1].split("\n", 1)
        if title_parts:
            title_match = title_parts[0].strip()
    
    title = title_match or "Security Incident"
    
    return {
        "criticality": criticality,
        "possibleDamage": "Potential data exposure, system compromise, and reputational damage to the organization.",
        "category": category,
        "riskDescription": f"If this {category.lower()} incident is not properly addressed, it may lead to unauthorized access to sensitive data, financial loss, and regulatory penalties.",
        "riskLikelihood": likelihood_score,
        "riskLikelihoodJustification": likelihood_justification,
        "riskImpact": impact_score,
        "riskImpactJustification": impact_justification,
        "riskExposureRating": "High Exposure",
        "riskPriority": priority,
        "riskAppetite": "Exceeds Appetite",
        "riskMitigation": [
            "Step 1: Isolate affected systems to prevent further compromise",
            "Step 2: Initiate incident response procedures according to the security policy",
            "Step 3: Notify relevant stakeholders and regulatory bodies if required",
            "Step 4: Perform forensic analysis to determine the extent of the breach",
            "Step 5: Implement remediation actions to address the vulnerability",
            "Step 6: Update security controls to prevent similar incidents",
            "Step 7: Conduct post-incident review and update documentation"
        ]
    } 
