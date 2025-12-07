import json
import re
import random
import traceback
import os
from openai import OpenAI
from django.conf import settings

class OpenAIIntegration:
    """OpenAI integration class for incident analysis"""
    
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
                print("✅ OpenAI client initialized successfully")
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
                        "content": "You are a senior cybersecurity analyst specializing in banking GRC (Governance, Risk, and Compliance) systems. You provide detailed, structured incident analysis in JSON format."
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

def analyze_incident_comprehensive(incident_title, incident_description):
    """
    Comprehensive incident analysis for GRC banking system with extensive banking-specific analysis.
    
    Args:
        incident_title (str): Title of the incident
        incident_description (str): Detailed description of the incident
    
    Returns:
        dict: JSON object containing comprehensive incident analysis
    """
    try:
        # Initialize OpenAI integration
        print("🔄 Using OpenAI for incident analysis")
        openai_client = OpenAIIntegration()
        
        if not openai_client.is_available:
            print("⚠️ OpenAI not available, falling back to comprehensive fallback analysis")
            return generate_comprehensive_fallback_analysis(incident_title, incident_description)

        # Create a comprehensive prompt for banking GRC incident analysis optimized for OpenAI
        prompt = f"""Analyze the following security incident for a banking GRC system and provide a comprehensive JSON response.

**INCIDENT DETAILS:**
- Title: {incident_title}
- Description: {incident_description}

**REQUIRED JSON STRUCTURE:**
{{
  "riskPriority": "<P0/P1/P2/P3>",
  "criticality": "<Critical/High/Medium/Low>",
  "costOfIncident": <single_numeric_value>,
  "costJustification": "<detailed explanation of cost calculation>",
  "possibleDamage": "<detailed banking-specific impact analysis>",
  "systemsInvolved": ["<system1>", "<system2>", "..."],
  "initialImpactAssessment": "<technical and business impact details>",
  "mitigationSteps": ["<step1>", "<step2>", "..."],
  "comments": "<expert analysis with regulatory context>",
  "violatedPolicies": ["<policy1>", "<policy2>", "..."],
  "procedureControlFailures": ["<control1>", "<control2>", "..."],
  "lessonsLearned": ["<lesson1>", "<lesson2>", "..."]
}}

**CLASSIFICATION GUIDELINES:**

**Risk Priority:**
- P0: Critical banking operations down, >10K customers affected, >$1M regulatory penalty
- P1: Significant impact, 1K-10K customers affected, $100K-$1M penalty
- P2: Limited impact, <1K customers affected
- P3: Minor impact, internal only

**Criticality:**
- Critical: Core banking systems, payment rails, transaction processing
- High: Trading platforms, risk management, customer-facing apps
- Medium: Internal applications, reporting systems
- Low: Development/test environments

**Banking Context to Consider:**
- Regulatory frameworks: FFIEC, OCC, FRB, FDIC, CFPB
- Compliance requirements: GLBA, BSA/AML, SOX, PCI DSS, NYDFS Cybersecurity, Basel III
- Banking systems: Core Banking, Payment Processing, Digital Banking, Trading Systems, Risk Management, Compliance Systems, ATM Networks, Wire Transfer Systems

**Analysis Requirements:**
1. **costOfIncident**: Provide ONLY a single numeric value (no currency symbols, no ranges) representing total estimated cost in USD. Examples: 50000, 250000, 1500000
2. **costJustification**: Provide detailed breakdown explaining: regulatory fines estimate, operational costs (downtime, recovery), remediation costs (technical fixes, security improvements), customer compensation, reputational damage costs, legal fees, and how you arrived at the total number
3. Possible damage should cover: operational disruption, customer impact, regulatory penalties, reputational harm
4. Systems involved should list specific banking infrastructure components
5. Mitigation steps should include: immediate containment, customer communication, regulatory notification, forensics, recovery
6. Violated policies should reference specific banking security/compliance policies
7. Control failures should identify which security controls failed
8. Lessons learned should provide actionable recommendations

**CRITICAL:** The costOfIncident MUST be a pure numeric value (integer) without any currency symbols, commas, or text. Example: 250000 NOT "$250,000" or "250000 USD"

Provide ONLY the JSON response, no additional text."""

        # Process the incident using OpenAI
        print(f"📊 Analyzing incident: {incident_title}")
        model = getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo')
        response = openai_client.generate_response(prompt, model=model, max_tokens=2000, temperature=0.3)
        
        # Check if response is None (API error)
        if response is None:
            print("❌ OpenAI request failed, falling back to comprehensive fallback analysis")
            return generate_comprehensive_fallback_analysis(incident_title, incident_description)
       
        # Parse the JSON from the response
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
                'riskPriority', 'criticality', 'costOfIncident', 'costJustification', 'possibleDamage', 
                             'systemsInvolved', 'initialImpactAssessment', 'mitigationSteps', 
                'comments', 'violatedPolicies', 'procedureControlFailures', 'lessonsLearned'
            ]
            
            missing_fields = [field for field in required_fields if field not in incident_analysis]
            
            if missing_fields:
                print(f"⚠️ Missing required fields in AI response: {missing_fields}")
                print("Falling back to comprehensive fallback analysis")
                return generate_comprehensive_fallback_analysis(incident_title, incident_description)
            
            # Ensure list fields are actually lists
            list_fields = ['systemsInvolved', 'mitigationSteps', 'violatedPolicies', 
                          'procedureControlFailures', 'lessonsLearned']
            for field in list_fields:
                if not isinstance(incident_analysis.get(field), list):
                    # Convert to list if it's a string
                    if isinstance(incident_analysis.get(field), str):
                        incident_analysis[field] = [incident_analysis[field]]
                    else:
                        print(f"⚠️ Field {field} is not a list, falling back")
                        return generate_comprehensive_fallback_analysis(incident_title, incident_description)
            
            print(f"✅ Successfully parsed comprehensive banking GRC incident analysis")
            return incident_analysis
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"Response text: {response[:500]}...")  # Print first 500 chars for debugging
            return generate_comprehensive_fallback_analysis(incident_title, incident_description)
        except Exception as e:
            print(f"❌ Error processing response: {e}")
            traceback.print_exc()
            return generate_comprehensive_fallback_analysis(incident_title, incident_description)

    except Exception as e:
        print(f"❌ Error with OpenAI processing: {e}")
        traceback.print_exc()
        return generate_comprehensive_fallback_analysis(incident_title, incident_description)

def generate_comprehensive_fallback_analysis(incident_title, incident_description):
    """Generate a comprehensive fallback analysis when the AI model is unavailable."""
    # Extract some keywords from the incident for basic categorization
    description_lower = (incident_title + " " + incident_description).lower()
    
    # Default values
    risk_priority = "P1"
    criticality = "Medium"
    cost_estimate = 150000
    cost_justification = "Estimated based on typical incident response costs including system recovery, investigation, and remediation efforts."
    systems = ["Core Banking System", "Network Infrastructure"]
    
    # Basic categorization based on keywords and assign appropriate values
    if any(word in description_lower for word in ["breach", "leak", "exposed", "data", "sensitive", "customer"]):
        risk_priority = "P0"
        criticality = "Critical"
        cost_estimate = 2500000
        cost_justification = "Data breach incident cost breakdown: Regulatory fines ($1,000,000 - GDPR/PCI DSS violations), Forensic investigation and remediation ($500,000), Customer notification and credit monitoring ($300,000), Legal fees and settlements ($400,000), Reputational damage and customer loss ($300,000). Total estimated impact: $2,500,000"
        systems = ["Core Banking System", "Customer Database", "Online Banking Platform", "Data Warehouse"]
        possible_damage = "Massive customer data exposure, regulatory penalties up to $50M, severe reputational damage, potential class-action lawsuits, loss of customer trust, and business continuity threats."
        violated_policies = ["Data Protection Policy", "Customer Privacy Policy", "Information Security Policy", "Incident Response Policy"]
        control_failures = ["Data encryption controls", "Access control mechanisms", "Data loss prevention systems", "Network segmentation controls"]
        
    elif any(word in description_lower for word in ["malware", "virus", "ransomware", "trojan", "attack"]):
        risk_priority = "P0"
        criticality = "Critical"
        cost_estimate = 800000
        cost_justification = "Malware/Ransomware incident breakdown: System recovery and restoration ($250,000), Business downtime and lost revenue ($200,000), Incident response and forensics ($150,000), Security infrastructure upgrades ($100,000), Ransom payment consideration ($50,000), Staff overtime and emergency response ($50,000). Total: $800,000"
        systems = ["Core Banking System", "ATM Network", "Payment Processing System", "Email System"]
        possible_damage = "System disruption, potential data encryption, business operations halt, customer service interruption, and recovery costs."
        violated_policies = ["Malware Protection Policy", "System Security Policy", "Business Continuity Policy"]
        control_failures = ["Antivirus protection", "Email filtering systems", "Network intrusion detection", "Endpoint protection controls"]
        
    elif any(word in description_lower for word in ["phish", "social engineering", "fraud", "impersonation"]):
        risk_priority = "P1"
        criticality = "High"
        cost_estimate = 350000
        cost_justification = "Phishing/Social engineering costs: Direct financial fraud losses ($100,000), Account recovery and customer reimbursement ($80,000), Enhanced security training programs ($50,000), Additional authentication controls ($70,000), Investigation and legal costs ($50,000). Total: $350,000"
        systems = ["Email System", "Online Banking Platform", "Employee Workstations", "Authentication System"]
        possible_damage = "Credential theft, unauthorized access to customer accounts, potential financial fraud, and employee security awareness gaps."
        violated_policies = ["Email Security Policy", "Authentication Policy", "Employee Training Policy", "Fraud Prevention Policy"]
        control_failures = ["Email security controls", "Multi-factor authentication", "User awareness training", "Fraud detection systems"]
        
    elif any(word in description_lower for word in ["unauthorized", "access", "privilege", "credential", "insider"]):
        risk_priority = "P1"
        criticality = "High"
        cost_estimate = 450000
        cost_justification = "Unauthorized access incident costs: Forensic investigation ($100,000), Data integrity verification ($80,000), Access control system overhaul ($120,000), Legal and regulatory notifications ($70,000), Potential regulatory fines ($50,000), Internal investigation and HR costs ($30,000). Total: $450,000"
        systems = ["Core Banking System", "Privileged Access Management", "Active Directory", "Database Systems"]
        possible_damage = "Unauthorized access to sensitive data, privilege escalation, potential data theft, and insider threat materialization."
        violated_policies = ["Access Control Policy", "Privileged Access Policy", "Identity Management Policy", "Segregation of Duties Policy"]
        control_failures = ["Access control systems", "Privilege management controls", "User access reviews", "Segregation of duties controls"]
        
    elif any(word in description_lower for word in ["compliance", "regulatory", "audit", "violation"]):
        risk_priority = "P1"
        criticality = "High"
        cost_estimate = 1200000
        cost_justification = "Regulatory compliance violation costs: Direct regulatory fines ($500,000), Compliance audit and remediation ($250,000), Enhanced monitoring and reporting systems ($200,000), Legal and consulting fees ($150,000), Process improvements and training ($100,000). Total: $1,200,000"
        systems = ["Compliance Management System", "Audit Trail System", "Reporting System", "Document Management"]
        possible_damage = "Regulatory fines, enforcement actions, audit findings, reputational damage, and increased regulatory scrutiny."
        violated_policies = ["Regulatory Compliance Policy", "Audit Policy", "Documentation Policy", "Reporting Policy"]
        control_failures = ["Compliance monitoring controls", "Audit trail mechanisms", "Regulatory reporting controls", "Documentation controls"]
        
    else:
        # Default case
        possible_damage = "Potential operational disruption, security compromise, and moderate business impact requiring immediate attention."
        violated_policies = ["Information Security Policy", "Incident Response Policy", "Risk Management Policy"]
        control_failures = ["Security monitoring controls", "Incident detection systems", "Risk assessment procedures"]
    
    return {
        "riskPriority": risk_priority,
        "criticality": criticality,
        "costOfIncident": cost_estimate,
        "costJustification": cost_justification,
        "possibleDamage": possible_damage,
        "systemsInvolved": systems,
        "initialImpactAssessment": f"Incident '{incident_title}' has been identified with potential impact on critical banking operations. Immediate containment and investigation required to determine full scope and prevent escalation.",
        "mitigationSteps": [
            "Step 1: Activate incident response team and establish command center",
            "Step 2: Isolate affected systems to prevent further compromise or spread",
            "Step 3: Preserve evidence and maintain chain of custody for forensic analysis",
            "Step 4: Assess immediate business impact and implement business continuity measures",
            "Step 5: Notify key stakeholders including senior management and legal team",
            "Step 6: Conduct preliminary investigation to determine root cause and scope",
            "Step 7: Implement temporary controls and workarounds to restore operations",
            "Step 8: Engage external experts if specialized skills are required",
            "Step 9: Prepare regulatory notifications if required by compliance obligations",
            "Step 10: Document all actions taken and maintain incident timeline",
            "Step 11: Conduct post-incident review and implement lessons learned",
            "Step 12: Update security controls and procedures to prevent recurrence"
        ],
        "comments": f"This incident requires immediate attention due to its potential impact on banking operations. The analysis is based on the incident title '{incident_title}' and available description. Further investigation may reveal additional complexities requiring escalated response measures.",
        "violatedPolicies": violated_policies,
        "procedureControlFailures": control_failures,
        "lessonsLearned": [
            "Importance of rapid incident detection and response capabilities",
            "Need for regular security awareness training and testing",
            "Critical role of backup and recovery procedures in business continuity",
            "Value of comprehensive incident documentation for future reference",
            "Necessity of regular security control testing and validation",
            "Importance of clear communication channels during incident response",
            "Need for regular review and update of incident response procedures",
            "Critical importance of stakeholder notification and regulatory compliance"
        ]
    }