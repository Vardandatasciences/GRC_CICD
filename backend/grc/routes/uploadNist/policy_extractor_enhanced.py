#!/usr/bin/env python3
"""
Enhanced Policy and Subpolicy Extractor using OpenAI API
Analyzes extracted sections to identify and extract policies and subpolicies with comprehensive metadata.
Generates: Scope, Objective, PolicyType, PolicyCategory, PolicySubCategory, Identifiers, Framework metadata
"""

import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import openai
from openai import OpenAI
import time
from datetime import datetime, date

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[INFO] Loaded environment variables from .env file")
except ImportError:
    print("[INFO] python-dotenv not installed. Install with: pip install python-dotenv")
    print("[INFO] Falling back to system environment variables")

# Configuration - Use Django settings
from django.conf import settings
OPENAI_API_KEY = getattr(settings, 'OPENAI_API_KEY', None)
# Clean model name - strip quotes and whitespace to avoid "invalid model ID" errors
MODEL_NAME_RAW = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
MODEL_NAME = str(MODEL_NAME_RAW).strip().strip('"').strip("'")
SECTIONS_DIR = "sections_out_tcfd"
OUTPUT_DIR = "policies_extracted_tcfd_UPDATED_ENHANCED_NEW"

class EnhancedPolicyExtractor:
    def __init__(self, api_key: str = None, model: str = MODEL_NAME):
        """Initialize the Enhanced PolicyExtractor with OpenAI API."""
        if not api_key:
            api_key = OPENAI_API_KEY
        if not api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in Django settings or pass api_key parameter.")
        
        self.client = OpenAI(api_key=api_key)
        # Clean model name - strip quotes and whitespace
        self.model = str(model).strip().strip('"').strip("'")
        
        # Print configuration info similar to risk_instance_ai.py
        if OPENAI_API_KEY:
            print(f"🌐 OpenAI Configuration for Policy Extractor:")
            print(f"   Model (original): '{MODEL_NAME_RAW}'")
            print(f"   Model (cleaned): '{self.model}'")
            print(f"   API Key: {'*' * (len(OPENAI_API_KEY) - 4) + OPENAI_API_KEY[-4:]}")
        else:
            print("⚠️  WARNING: OPENAI_API_KEY not found in Django settings!")
            print("   Please set OPENAI_API_KEY in your Django settings.")
        
        # Framework detection and metadata
        self.framework_metadata = {}
        self.policy_id_counter = 1
        self.subpolicy_id_counter = 1
        
    def detect_framework_info(self, sections_dir: str) -> Dict[str, Any]:
        """Detect framework information from directory name and structure."""
        dir_name = Path(sections_dir).name.upper()
        
        # Framework detection patterns
        if "PCI" in dir_name or "DSS" in dir_name:
            return {
                "framework_name": "Payment Card Industry Data Security Standard (PCI DSS)",
                "current_version": "4.0",
                "framework_description": "The Payment Card Industry Data Security Standard (PCI DSS) is a set of security standards designed to ensure that all companies that accept, process, store or transmit credit card information maintain a secure environment. PCI DSS applies to all entities involved in payment card processing including merchants, processors, acquirers, issuers, and service providers.",
                "category": "Financial Security and Compliance",
                "start_date": "2022-03-31",
                "end_date": None,  # Active standard
                "identifier_prefix": "PCI-DSS"
            }
        elif "NIST" in dir_name:
            if "CSF" in dir_name:
                return {
                    "framework_name": "NIST Cybersecurity Framework (CSF)",
                    "current_version": "2.0",
                    "framework_description": "The NIST Cybersecurity Framework provides a policy framework of computer security guidance for how private sector organizations in the United States can assess and improve their ability to prevent, detect, and respond to cyber attacks. It consists of standards, guidelines, and practices to promote the protection of critical infrastructure.",
                    "category": "Cybersecurity Risk Management",
                    "start_date": "2024-02-26",
                    "end_date": None,
                    "identifier_prefix": "NIST-CSF"
                }
            else:
                return {
                    "framework_name": "NIST SP 800-53 Security and Privacy Controls",
                    "current_version": "5.0",
                    "framework_description": "NIST Special Publication 800-53 provides a catalog of security and privacy controls for federal information systems and organizations to protect organizational operations and assets, individuals, other organizations, and the Nation from a diverse set of threats including hostile attacks, human errors, natural disasters, structural failures, foreign intelligence entities, and privacy risks.",
                    "category": "Security and Privacy Controls",
                    "start_date": "2020-09-23",
                    "end_date": None,
                    "identifier_prefix": "NIST-800-53"
                }
        elif "GRI" in dir_name:
            return {
                "framework_name": "Global Reporting Initiative (GRI) Standards",
                "current_version": "2021",
                "framework_description": "The GRI Standards are the most widely used standards for sustainability reporting. They feature a modular, interrelated structure, and represent the global best practice for reporting on a range of economic, environmental and social impacts. The Standards are designed to enhance the global comparability and quality of information on these impacts.",
                "category": "Sustainability and ESG Reporting",
                "start_date": "2021-01-01",
                "end_date": None,
                "identifier_prefix": "GRI"
            }
        elif "TCFD" in dir_name:
            return {
                "framework_name": "Task Force on Climate-related Financial Disclosures (TCFD)",
                "current_version": "2023",
                "framework_description": "The Task Force on Climate-related Financial Disclosures (TCFD) provides recommendations for more effective climate-related disclosures that could promote more informed investment, credit, and insurance underwriting decisions and, in turn, enable stakeholders to understand better the concentrations of carbon-related assets in the financial sector and the financial system's exposures to climate-related risks.",
                "category": "Climate Risk and Financial Disclosure",
                "start_date": "2017-06-29",
                "end_date": None,
                "identifier_prefix": "TCFD"
            }
        elif "HIPAA" in dir_name:
            return {
                "framework_name": "Health Insurance Portability and Accountability Act (HIPAA)",
                "current_version": "2013",
                "framework_description": "The Health Insurance Portability and Accountability Act (HIPAA) sets the standard for sensitive patient data protection. Companies that deal with protected health information (PHI) must have physical, network, and process security measures in place and follow them to ensure HIPAA compliance.",
                "category": "Healthcare Privacy and Security",
                "start_date": "2013-01-17",
                "end_date": None,
                "identifier_prefix": "HIPAA"
            }
        else:
            return {
                "framework_name": "Custom Policy Framework",
                "current_version": "1.0",
                "framework_description": "A comprehensive policy framework designed to establish governance, compliance, and operational standards for organizational activities. This framework provides structured guidance for policy development, implementation, and monitoring across various business functions.",
                "category": "General Policy Framework",
                "start_date": date.today().strftime("%Y-%m-%d"),
                "end_date": None,
                "identifier_prefix": "POL"
            }
    
    def categorize_policy_comprehensive(self, policy_title: str, policy_description: str, section_title: str = "") -> Tuple[str, str, str]:
        """Comprehensive policy categorization with detailed subcategories."""
        title_lower = policy_title.lower()
        desc_lower = policy_description.lower()
        section_lower = section_title.lower()
        
        combined_text = f"{title_lower} {desc_lower} {section_lower}"
        
        # Security policies with detailed subcategories
        if any(keyword in combined_text for keyword in ['security', 'access', 'authentication', 'authorization', 'encryption', 'firewall', 'vulnerability', 'threat', 'malware', 'antivirus']):
            if any(keyword in combined_text for keyword in ['access', 'authentication', 'authorization', 'identity', 'user', 'login', 'password']):
                return "Security", "Access Control and Identity Management", "Identity and Authentication"
            elif any(keyword in combined_text for keyword in ['network', 'firewall', 'intrusion', 'perimeter', 'segmentation']):
                return "Security", "Network Security", "Perimeter Protection and Monitoring"
            elif any(keyword in combined_text for keyword in ['data', 'encryption', 'cryptography', 'key management', 'classification']):
                return "Security", "Data Protection", "Information Security and Encryption"
            elif any(keyword in combined_text for keyword in ['vulnerability', 'patch', 'scanning', 'assessment']):
                return "Security", "Vulnerability Management", "Security Assessment and Remediation"
            elif any(keyword in combined_text for keyword in ['incident', 'response', 'forensics', 'breach']):
                return "Security", "Incident Response", "Security Incident Management"
            else:
                return "Security", "General Security Controls", "Security Governance"
        
        # Compliance policies with regulatory focus
        elif any(keyword in combined_text for keyword in ['compliance', 'regulatory', 'audit', 'standard', 'requirement', 'certification']):
            if any(keyword in combined_text for keyword in ['pci', 'payment', 'card', 'financial']):
                return "Compliance", "Financial Regulations", "Payment Card Industry Standards"
            elif any(keyword in combined_text for keyword in ['privacy', 'gdpr', 'hipaa', 'personal data']):
                return "Compliance", "Privacy Regulations", "Data Protection Laws"
            elif any(keyword in combined_text for keyword in ['sox', 'sarbanes', 'financial reporting']):
                return "Compliance", "Financial Reporting", "Corporate Governance"
            else:
                return "Compliance", "Regulatory Compliance", "Standards Adherence"
        
        # Risk Management policies
        elif any(keyword in combined_text for keyword in ['risk', 'threat', 'assessment', 'mitigation', 'management']):
            if any(keyword in combined_text for keyword in ['business continuity', 'disaster recovery', 'continuity']):
                return "Risk Management", "Business Continuity", "Disaster Recovery Planning"
            elif any(keyword in combined_text for keyword in ['vendor', 'supplier', 'third party', 'outsourcing']):
                return "Risk Management", "Third-Party Risk", "Vendor Risk Management"
            else:
                return "Risk Management", "Enterprise Risk Management", "Risk Assessment and Mitigation"
        
        # Privacy policies
        elif any(keyword in combined_text for keyword in ['privacy', 'personal', 'pii', 'phi', 'cardholder', 'patient', 'customer data']):
            if any(keyword in combined_text for keyword in ['health', 'medical', 'patient', 'phi']):
                return "Privacy", "Healthcare Privacy", "Protected Health Information"
            elif any(keyword in combined_text for keyword in ['payment', 'card', 'financial', 'cardholder']):
                return "Privacy", "Financial Privacy", "Payment Card Data Protection"
            else:
                return "Privacy", "Data Privacy", "Personal Information Protection"
        
        # Operational policies
        elif any(keyword in combined_text for keyword in ['operational', 'procedure', 'process', 'workflow', 'management', 'administration']):
            if any(keyword in combined_text for keyword in ['change', 'configuration', 'deployment']):
                return "Operations", "Change Management", "Configuration and Deployment"
            elif any(keyword in combined_text for keyword in ['monitoring', 'logging', 'audit trail']):
                return "Operations", "Monitoring and Logging", "System Monitoring"
            else:
                return "Operations", "Operational Procedures", "Process Management"
        
        # Governance policies
        elif any(keyword in combined_text for keyword in ['governance', 'oversight', 'management', 'leadership', 'board']):
            return "Governance", "Corporate Governance", "Executive Oversight"
        
        # Training and awareness
        elif any(keyword in combined_text for keyword in ['training', 'awareness', 'education', 'competency']):
            return "Human Resources", "Training and Awareness", "Security Education"
        
        # Physical security
        elif any(keyword in combined_text for keyword in ['physical', 'facility', 'premises', 'building', 'access control']):
            return "Security", "Physical Security", "Facility Access Control"
        
        # Default categorization
        else:
            return "General", "Policy Management", "General Requirements"
    
    def generate_comprehensive_scope(self, policy_title: str, policy_description: str, section_title: str = "") -> str:
        """Generate comprehensive scope statement for policies."""
        policy_type, category, subcategory = self.categorize_policy_comprehensive(policy_title, policy_description, section_title)
        
        base_scope = f"This policy applies to all organizational units, personnel, systems, and processes involved in {policy_title.lower()}. "
        
        # Add specific scope based on policy type
        if policy_type == "Security":
            scope_addition = "The scope encompasses all information systems, networks, applications, databases, and associated infrastructure components. It includes all employees, contractors, vendors, and third-party service providers who have access to organizational systems or data. The policy covers both on-premises and cloud-based environments, including mobile devices and remote access scenarios."
        elif policy_type == "Compliance":
            scope_addition = "The scope includes all business processes, documentation, reporting mechanisms, and personnel responsibilities related to regulatory compliance. It encompasses all organizational levels from executive leadership to operational staff, covering both direct and indirect compliance activities. The policy applies to all jurisdictions where the organization operates and all applicable regulatory requirements."
        elif policy_type == "Privacy":
            scope_addition = "The scope covers all personal data, sensitive information, and privacy-related processes throughout the data lifecycle from collection to disposal. It applies to all systems that store, process, or transmit personal information, including backup systems and archived data. The policy encompasses all personnel who handle personal data and all third parties with access to such information."
        elif policy_type == "Risk Management":
            scope_addition = "The scope includes all organizational assets, business processes, and operational activities that may be subject to risk. It covers all risk categories including operational, financial, strategic, and reputational risks. The policy applies to all organizational levels and includes both internal operations and external partnerships or vendor relationships."
        else:
            scope_addition = "The scope encompasses all relevant organizational activities, systems, and personnel as determined by the policy requirements. It includes all operational environments and applies to all stakeholders who may be affected by or responsible for policy implementation."
        
        return base_scope + scope_addition
    
    def generate_comprehensive_objective(self, policy_title: str, policy_description: str, policy_type: str) -> str:
        """Generate comprehensive objective statement for policies."""
        base_objective = f"The primary objective of this policy is to establish clear requirements and guidelines for {policy_title.lower()}, ensuring organizational compliance and operational effectiveness. "
        
        # Add specific objectives based on policy type
        if policy_type == "Security":
            specific_objectives = "Specific objectives include: (1) protecting organizational assets from unauthorized access, modification, or destruction; (2) ensuring the confidentiality, integrity, and availability of information systems and data; (3) establishing robust security controls and monitoring mechanisms; (4) maintaining compliance with applicable security standards and regulations; (5) enabling secure business operations while minimizing security risks; and (6) fostering a security-conscious organizational culture through awareness and training."
        elif policy_type == "Compliance":
            specific_objectives = "Specific objectives include: (1) ensuring adherence to all applicable laws, regulations, and industry standards; (2) establishing systematic compliance monitoring and reporting processes; (3) minimizing regulatory and legal risks through proactive compliance management; (4) maintaining accurate documentation and evidence of compliance activities; (5) enabling effective communication with regulators and auditors; and (6) promoting a culture of compliance throughout the organization."
        elif policy_type == "Privacy":
            specific_objectives = "Specific objectives include: (1) protecting the privacy rights of individuals whose personal information is processed; (2) ensuring lawful and transparent collection, use, and disclosure of personal data; (3) implementing appropriate technical and organizational measures to safeguard personal information; (4) enabling individuals to exercise their privacy rights effectively; (5) maintaining compliance with applicable privacy laws and regulations; and (6) building trust through responsible data stewardship practices."
        elif policy_type == "Risk Management":
            specific_objectives = "Specific objectives include: (1) identifying, assessing, and prioritizing organizational risks across all business areas; (2) implementing effective risk mitigation strategies and controls; (3) establishing risk monitoring and reporting mechanisms; (4) ensuring business continuity and resilience in the face of potential threats; (5) optimizing risk-return trade-offs in business decision-making; and (6) maintaining stakeholder confidence through effective risk management."
        else:
            specific_objectives = "Specific objectives include: (1) establishing clear expectations and requirements for organizational behavior; (2) ensuring consistent implementation of best practices across all applicable areas; (3) minimizing operational risks and compliance gaps; (4) promoting accountability and responsibility among all stakeholders; (5) enabling effective monitoring and continuous improvement; and (6) supporting overall organizational objectives and strategic goals."
        
        return base_objective + specific_objectives
    
    def generate_structured_identifiers(self, framework_prefix: str, policy_title: str, policy_type: str) -> Tuple[str, int]:
        """Generate structured identifiers for policies."""
        # Create policy type abbreviations
        type_abbrev = {
            "Security": "SEC",
            "Compliance": "COMP",
            "Privacy": "PRIV", 
            "Risk Management": "RISK",
            "Operations": "OPS",
            "Governance": "GOV",
            "Human Resources": "HR",
            "General": "GEN"
        }.get(policy_type, "GEN")
        
        # Generate policy identifier
        policy_id = f"{framework_prefix}-{type_abbrev}-{self.policy_id_counter:03d}"
        current_policy_id = self.policy_id_counter
        self.policy_id_counter += 1
        
        return policy_id, current_policy_id
    
    def generate_subpolicy_identifier(self, policy_id: str, subpolicy_index: int) -> str:
        """Generate structured identifier for subpolicies."""
        return f"{policy_id}.{subpolicy_index:02d}"
    
    def chunk_content(self, content: str, max_chunk_size: int = 8000) -> List[str]:
        """Split content into chunks to handle large sections without losing information."""
        if len(content) <= max_chunk_size:
            return [content]
        
        chunks = []
        words = content.split()
        current_chunk = []
        current_size = 0
        
        for word in words:
            word_size = len(word) + 1
            if current_size + word_size > max_chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = word_size
            else:
                current_chunk.append(word)
                current_size += word_size
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

    def analyze_content_for_policies_enhanced(self, content: str, section_title: str, framework_info: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """Enhanced policy analysis with comprehensive metadata generation."""
        
        system_prompt = f"""You are an expert policy analyst specializing in {framework_info['framework_name']}. Your task is to analyze content and generate comprehensive policy and subpolicy information with detailed metadata.

FRAMEWORK CONTEXT:
- Framework: {framework_info['framework_name']}
- Version: {framework_info['current_version']}
- Category: {framework_info['category']}
- Description: {framework_info['framework_description']}

CRITICAL REQUIREMENTS:
1. Every policy MUST have at least one subpolicy
2. Every subpolicy MUST have a detailed "control" field
3. Generate comprehensive metadata for all policies and subpolicies
4. Create structured, implementable policies from the content

ENHANCED FIELD REQUIREMENTS:
For each POLICY, generate:
- policy_id: Structured identifier (will be overridden with framework-specific format)
- policy_title: Clear, specific title
- policy_description: Comprehensive 3-4 sentence description explaining purpose, importance, and scope
- policy_text: Complete policy statement with detailed requirements
- scope: Detailed scope statement covering all applicable areas, systems, and personnel
- objective: Comprehensive objective statement with specific goals and outcomes
- policy_type: High-level category (Security/Compliance/Privacy/Risk Management/Operations/Governance/HR/General)
- policy_category: Mid-level category within the type
- policy_subcategory: Specific subcategory for detailed classification
- subpolicies: Array of detailed subpolicies

For each SUBPOLICY, generate:
- subpolicy_id: Structured identifier (will be enhanced with parent policy reference)
- subpolicy_title: Specific implementation area
- subpolicy_description: Comprehensive implementation requirements
- control: Detailed control statement with WHO, WHAT, WHEN, HOW, WHERE

POLICY CATEGORIZATION GUIDELINES:
- Security: Access control, data protection, network security, vulnerability management, incident response
- Compliance: Regulatory adherence, audit requirements, standards compliance, reporting
- Privacy: Data privacy, personal information protection, consent management
- Risk Management: Risk assessment, business continuity, vendor management, threat management
- Operations: Process management, change control, monitoring, system administration
- Governance: Executive oversight, policy management, strategic alignment
- Human Resources: Training, awareness, personnel security, competency management
- General: Broad organizational policies, general requirements

SCOPE GENERATION GUIDELINES:
Generate detailed scope statements that specify:
- Organizational units and personnel covered
- Systems, applications, and infrastructure included
- Geographic and jurisdictional coverage
- Third-party and vendor relationships
- Data types and information categories
- Operational environments (on-premises, cloud, mobile, remote)

OBJECTIVE GENERATION GUIDELINES:
Create comprehensive objectives that include:
- Primary policy purpose and goals
- Specific measurable outcomes
- Compliance and regulatory objectives
- Risk mitigation goals
- Operational effectiveness targets
- Stakeholder protection measures

CONTROL STATEMENT REQUIREMENTS:
Each control must specify:
1. WHAT: Specific actions, processes, or measures to implement
2. WHO: Responsible roles, departments, or individuals
3. WHEN: Frequency, timelines, deadlines, or triggers
4. HOW: Methods, procedures, tools, or measurement criteria
5. WHERE: Applicable scope, systems, locations, or organizational units

Return ONLY valid JSON in this exact format:
{{
  "has_policies": true/false,
  "framework_info": {{
    "framework_name": "{framework_info['framework_name']}",
    "current_version": "{framework_info['current_version']}",
    "category": "{framework_info['category']}"
  }},
  "policies": [
    {{
      "policy_id": "string",
      "policy_title": "string",
      "policy_description": "comprehensive 3-4 sentence description",
      "policy_text": "complete policy statement",
      "scope": "detailed scope statement covering all applicable areas",
      "objective": "comprehensive objective with specific goals",
      "policy_type": "Security/Compliance/Privacy/Risk Management/Operations/Governance/HR/General",
      "policy_category": "mid-level category",
      "policy_subcategory": "specific subcategory",
      "subpolicies": [
        {{
          "subpolicy_id": "string",
          "subpolicy_title": "string",
          "subpolicy_description": "comprehensive implementation requirements",
          "control": "detailed control with WHO/WHAT/WHEN/HOW/WHERE"
        }}
      ]
    }}
  ],
  "document_type": "regulation/standard/guideline/control_framework/policy_generated/other",
  "confidence": 0.0-1.0
}}

IMPORTANT:
- Generate policies that are specific to {framework_info['framework_name']} context
- Ensure all metadata fields are comprehensive and detailed
- Make policies actionable and measurable
- Include specific implementation guidance in controls
- Return ONLY the JSON, no additional text"""

        # Handle large content by chunking
        content_chunks = self.chunk_content(content)
        all_policies = []
        document_types = []
        confidences = []
        
        for i, chunk in enumerate(content_chunks):
            user_prompt = f"""Section Title: {section_title}
Chunk {i+1} of {len(content_chunks)}

Content to analyze for {framework_info['framework_name']}:
{chunk}

Generate comprehensive policies with all required metadata fields. Focus on creating policies that are:
1. Specific to {framework_info['framework_name']} requirements
2. Actionable and measurable
3. Complete with detailed scope and objectives
4. Properly categorized and classified
5. Equipped with implementable controls

Ensure all policies have comprehensive metadata including scope, objective, categorization, and structured identifiers."""

            for attempt in range(max_retries):
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.1,
                        max_tokens=4000
                    )
                    
                    response_text = response.choices[0].message.content.strip()
                    
                    try:
                        result = json.loads(response_text)
                        
                        if result.get("has_policies", False):
                            # Enhance policies with structured identifiers and metadata
                            enhanced_policies = []
                            for policy in result.get("policies", []):
                                # Generate structured identifier
                                policy_id, policy_num = self.generate_structured_identifiers(
                                    framework_info['identifier_prefix'],
                                    policy.get('policy_title', ''),
                                    policy.get('policy_type', 'General')
                                )
                                
                                # Enhance policy with comprehensive metadata
                                enhanced_policy = {
                                    "policy_id": policy_id,
                                    "policy_title": policy.get('policy_title', ''),
                                    "policy_description": policy.get('policy_description', ''),
                                    "policy_text": policy.get('policy_text', ''),
                                    "scope": policy.get('scope') or self.generate_comprehensive_scope(
                                        policy.get('policy_title', ''),
                                        policy.get('policy_description', ''),
                                        section_title
                                    ),
                                    "objective": policy.get('objective') or self.generate_comprehensive_objective(
                                        policy.get('policy_title', ''),
                                        policy.get('policy_description', ''),
                                        policy.get('policy_type', 'General')
                                    ),
                                    "policy_type": policy.get('policy_type', 'General'),
                                    "policy_category": policy.get('policy_category', 'General Requirements'),
                                    "policy_subcategory": policy.get('policy_subcategory', 'General'),
                                    "subpolicies": []
                                }
                                
                                # Enhance subpolicies with structured identifiers
                                for j, subpolicy in enumerate(policy.get('subpolicies', []), 1):
                                    subpolicy_id = self.generate_subpolicy_identifier(policy_id, j)
                                    enhanced_subpolicy = {
                                        "subpolicy_id": subpolicy_id,
                                        "subpolicy_title": subpolicy.get('subpolicy_title', ''),
                                        "subpolicy_description": subpolicy.get('subpolicy_description', ''),
                                        "subpolicy_text": subpolicy.get('subpolicy_text', ''),
                                        "control": subpolicy.get('control', '')
                                    }
                                    enhanced_policy["subpolicies"].append(enhanced_subpolicy)
                                
                                enhanced_policies.append(enhanced_policy)
                            
                            all_policies.extend(enhanced_policies)
                            document_types.append(result.get("document_type", "other"))
                            confidences.append(result.get("confidence", 0.0))
                        break
                        
                    except json.JSONDecodeError as e:
                        print(f"[ERROR] Failed to parse JSON response for '{section_title}' chunk {i+1}, attempt {attempt+1}: {e}")
                        if attempt == max_retries - 1:
                            print(f"Response was: {response_text[:500]}...")
                        else:
                            time.sleep(1)
                            
                except Exception as e:
                    # Enhanced error logging for OpenAI API errors
                    error_msg = str(e)
                    print(f"[ERROR] OpenAI API call failed for '{section_title}' chunk {i+1}, attempt {attempt+1}: {error_msg}")
                    
                    # Check if it's an OpenAI API error with details
                    if hasattr(e, 'response') and hasattr(e.response, 'json'):
                        try:
                            error_data = e.response.json()
                            error_obj = error_data.get('error', {})
                            if isinstance(error_obj, dict):
                                error_detail = error_obj.get('message', 'Unknown error')
                                error_type = error_obj.get('type', 'Unknown type')
                                error_code = error_obj.get('code', 'Unknown code')
                                print(f"[ERROR] OpenAI Error Details:")
                                print(f"   Type: {error_type}")
                                print(f"   Code: {error_code}")
                                print(f"   Message: {error_detail}")
                                print(f"   Model sent: '{self.model}'")
                        except Exception:
                            pass
                    elif 'invalid model ID' in error_msg.lower() or '400' in error_msg:
                        print(f"[ERROR] Model ID issue detected!")
                        print(f"   Original model from settings: '{MODEL_NAME_RAW}'")
                        print(f"   Cleaned model: '{self.model}'")
                        print(f"   Please check OPENAI_MODEL in Django settings")
                    
                    if attempt == max_retries - 1:
                        print(f"[SKIP] Skipping chunk after {max_retries} attempts")
                    else:
                        wait_time = 2 ** attempt
                        print(f"[RETRY] Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
        
        # Combine results
        if all_policies:
            most_common_type = max(set(document_types), key=document_types.count) if document_types else "other"
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return {
                "has_policies": True,
                "framework_info": {
                    "framework_name": framework_info['framework_name'],
                    "current_version": framework_info['current_version'],
                    "framework_description": framework_info['framework_description'],
                    "category": framework_info['category'],
                    "start_date": framework_info['start_date'],
                    "end_date": framework_info['end_date']
                },
                "policies": all_policies,
                "document_type": most_common_type,
                "confidence": avg_confidence
            }
        else:
            return {
                "has_policies": False,
                "framework_info": {
                    "framework_name": framework_info['framework_name'],
                    "current_version": framework_info['current_version'],
                    "framework_description": framework_info['framework_description'],
                    "category": framework_info['category'],
                    "start_date": framework_info['start_date'],
                    "end_date": framework_info['end_date']
                },
                "policies": [],
                "document_type": "other",
                "confidence": 0.0
            }
    
    def process_section(self, section_path: Path, framework_info: Dict[str, Any], sections_base: Path = None) -> Optional[Dict[str, Any]]:
        """Process a single section folder and extract enhanced policies."""
        content_file = section_path / "content.json"
        if not content_file.exists():
            return None
        
        try:
            with open(content_file, 'r', encoding='utf-8') as f:
                section_data = json.load(f)
            
            section_title = section_data.get("name", section_path.name)
            content = section_data.get("content", "")
            
            if not content or len(content.strip()) < 50:
                print(f"[SKIP] Section '{section_title}' has insufficient content")
                return None
            
            print(f"[ANALYZING] {section_title}")
            
            # Enhanced analysis with framework context
            policy_analysis = self.analyze_content_for_policies_enhanced(content, section_title, framework_info)
            
            if policy_analysis.get("has_policies", False):
                # Compute relative path safely
                if sections_base:
                    try:
                        folder_path = str(section_path.relative_to(sections_base))
                    except ValueError:
                        folder_path = str(section_path.name)
                else:
                    folder_path = str(section_path.name)
                
                result = {
                    "section_info": {
                        "title": section_title,
                        "level": section_data.get("level"),
                        "start_page": section_data.get("start_page"),
                        "end_page": section_data.get("end_page"),
                        "folder_path": folder_path
                    },
                    "analysis": policy_analysis
                }
                
                # Enhanced statistics
                policies = policy_analysis.get('policies', [])
                total_subpolicies = sum(len(policy.get('subpolicies', [])) for policy in policies)
                total_controls = sum(
                    len([sp for sp in policy.get('subpolicies', []) if sp.get('control')]) 
                    for policy in policies
                )
                
                print(f"[FOUND] {len(policies)} policies, {total_subpolicies} subpolicies, {total_controls} controls in '{section_title}'")
                print(f"[METADATA] Generated comprehensive scope, objectives, and categorization")
                return result
            else:
                print(f"[NO POLICIES] '{section_title}'")
                return None
                
        except Exception as e:
            print(f"[ERROR] Processing section {section_path}: {e}")
            return None
    
    def extract_policies_from_sections_enhanced(self, sections_dir: str, output_dir: str = OUTPUT_DIR, resume: bool = True, verbose: bool = True):
        """Enhanced policy extraction with comprehensive metadata generation.
        
        Args:
            sections_dir: Directory containing extracted sections
            output_dir: Output directory for extracted policies
            resume: Whether to resume from previous extraction (for future use)
            verbose: Whether to print progress messages
            
        Returns:
            dict: Results containing:
                - success: bool indicating if extraction was successful
                - all_policies: list of extracted policies
                - summary: extraction summary with statistics
                - files: dict of saved file paths
                - error: error message if failed (optional)
        """
        sections_path = Path(sections_dir)
        if not sections_path.exists():
            raise FileNotFoundError(f"Sections directory not found: {sections_dir}")
        
        sections_folder = sections_path / "sections"
        if not sections_folder.exists():
            raise FileNotFoundError(f"Sections subfolder not found: {sections_folder}")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Detect framework information
        framework_info = self.detect_framework_info(sections_dir)
        
        if verbose:
            print(f"=== Enhanced Policy Extraction ===")
            print(f"Framework: {framework_info['framework_name']}")
            print(f"Version: {framework_info['current_version']}")
            print(f"Category: {framework_info['category']}")
            print(f"Using OpenAI model: {self.model}")
            print(f"Output directory: {output_path}")
        
        # Find all section folders
        all_section_paths = list(sections_folder.rglob("content.json"))
        total_sections = len(all_section_paths)
        
        if verbose:
            print(f"Found {total_sections} sections to process")
        
        all_policies = []
        processed_count = 0
        api_calls_count = 0
        
        for section_path in all_section_paths:
            section_folder = section_path.parent
            section_key = str(section_folder.relative_to(sections_folder))
            
            # Rate limiting
            if api_calls_count > 0:
                if api_calls_count % 50 == 0:
                    if verbose:
                        print(f"[INFO] Made {api_calls_count} API calls, taking longer break...")
                    time.sleep(10)
                elif api_calls_count % 10 == 0:
                    if verbose:
                        print(f"[INFO] Made {api_calls_count} API calls, brief pause...")
                    time.sleep(2)
                else:
                    time.sleep(0.5)
            
            if verbose:
                print(f"[PROCESSING] {processed_count + 1}/{total_sections}: {section_key}")
            
            try:
                result = self.process_section(section_folder, framework_info, sections_folder)
                if result:
                    all_policies.append(result)
                    policies_count = len(result['analysis']['policies'])
                    if verbose:
                        print(f"[SUCCESS] Generated {policies_count} enhanced policies with full metadata")
                else:
                    if verbose:
                        print(f"[NO POLICIES] No policies found")
                
                api_calls_count += 1
                
                # Save intermediate results
                if processed_count % 5 == 0 and all_policies:
                    with open(output_path / "all_policies_temp.json", 'w', encoding='utf-8') as f:
                        json.dump(all_policies, f, ensure_ascii=False, indent=2)
                
            except Exception as e:
                if verbose:
                    print(f"[ERROR] Failed to process {section_key}: {e}")
                
            processed_count += 1
        
        # Save final results with enhanced metadata
        if all_policies:
            # Save complete analysis
            all_policies_file = output_path / "all_policies.json"
            with open(all_policies_file, 'w', encoding='utf-8') as f:
                json.dump(all_policies, f, ensure_ascii=False, indent=2)
            
            # Enhanced summary with framework metadata
            total_policies = sum(len(item["analysis"]["policies"]) for item in all_policies)
            total_subpolicies = sum(
                sum(len(policy.get("subpolicies", [])) for policy in item["analysis"]["policies"]) 
                for item in all_policies
            )
            
            # Policy type distribution
            policy_types = {}
            for item in all_policies:
                for policy in item["analysis"]["policies"]:
                    policy_type = policy.get("policy_type", "General")
                    policy_types[policy_type] = policy_types.get(policy_type, 0) + 1
            
            summary = {
                "framework_metadata": framework_info,
                "extraction_summary": {
                    "total_sections_processed": len(all_policies),
                    "total_policies": total_policies,
                    "total_subpolicies": total_subpolicies,
                    "policy_type_distribution": policy_types,
                    "api_calls_made": api_calls_count,
                    "extraction_date": datetime.now().isoformat()
                }
            }
            
            summary_file = output_path / "extraction_summary.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            if verbose:
                print(f"\n=== ENHANCED EXTRACTION COMPLETE ===")
                print(f"Framework: {framework_info['framework_name']} v{framework_info['current_version']}")
                print(f"Total sections processed: {len(all_policies)}")
                print(f"Total policies generated: {total_policies}")
                print(f"Total subpolicies generated: {total_subpolicies}")
                print(f"Policy type distribution: {policy_types}")
                print(f"Files saved:")
                print(f"- {all_policies_file}")
                print(f"- {summary_file}")
            
            # Return results for programmatic use
            return {
                "success": True,
                "all_policies": all_policies,
                "summary": summary,
                "files": {
                    "all_policies": str(all_policies_file),
                    "summary": str(summary_file)
                }
            }
            
        else:
            if verbose:
                print("\n[NO POLICIES] No policies found in any sections")
            
            return {
                "success": False,
                "all_policies": [],
                "summary": {
                    "framework_metadata": framework_info,
                    "extraction_summary": {
                        "total_sections_processed": 0,
                        "total_policies": 0,
                        "total_subpolicies": 0,
                        "policy_type_distribution": {},
                        "api_calls_made": api_calls_count,
                        "extraction_date": datetime.now().isoformat()
                    }
                },
                "files": {}
            }

# Convenience function for easy importing and calling from other scripts
def extract_policies(sections_dir: str, 
                    output_dir: str = OUTPUT_DIR, 
                    api_key: str = None, 
                    model: str = MODEL_NAME,
                    verbose: bool = True) -> Dict[str, Any]:
    """
    Convenience function to extract policies from sections.
    This is the recommended function to call from other Python scripts.
    
    Args:
        sections_dir: Directory containing extracted sections
        output_dir: Output directory for extracted policies
        api_key: OpenAI API key (optional, defaults to OPENAI_API_KEY env var)
        model: OpenAI model to use (default: gpt-4o-mini)
        verbose: Whether to print progress messages
        
    Returns:
        dict: Results containing:
            - success: bool indicating if extraction was successful
            - all_policies: list of extracted policies
            - summary: extraction summary with statistics
            - files: dict of saved file paths
            
    Example:
        >>> from policy_extractor_enhanced import extract_policies
        >>> results = extract_policies(
        ...     sections_dir="sections_out_tcfd",
        ...     output_dir="policies_extracted",
        ...     verbose=True
        ... )
        >>> if results['success']:
        ...     print(f"Extracted {results['summary']['extraction_summary']['total_policies']} policies")
        ...     print(f"Files saved to: {results['files']}")
    """
    try:
        extractor = EnhancedPolicyExtractor(api_key=api_key, model=model)
        results = extractor.extract_policies_from_sections_enhanced(
            sections_dir=sections_dir,
            output_dir=output_dir,
            verbose=verbose
        )
        return results
    except Exception as e:
        return {
            "success": False,
            "all_policies": [],
            "summary": {},
            "files": {},
            "error": str(e)
        }


def main():
    """Main function to run enhanced policy extraction from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Policy Extraction with Comprehensive Metadata")
    parser.add_argument("--sections-dir", default=SECTIONS_DIR, help="Directory containing extracted sections")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Output directory for extracted policies")
    parser.add_argument("--api-key", help="OpenAI API key")
    parser.add_argument("--model", default=MODEL_NAME, help="OpenAI model to use")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress messages")
    
    args = parser.parse_args()
    
    try:
        results = extract_policies(
            sections_dir=args.sections_dir,
            output_dir=args.output_dir,
            api_key=args.api_key,
            model=args.model,
            verbose=not args.quiet
        )
        
        if results['success']:
            return 0
        else:
            print(f"[ERROR] {results.get('error', 'Extraction failed')}")
            return 1
            
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1

if __name__ == "__main__":
    exit(main())
