"""
Change Management Module for GRC System
Monitors for downloaded PDFs from Selenium, uploads to S3, and tracks amendments in Framework table
"""

import os
import json
import hashlib
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from difflib import get_close_matches

import PyPDF2

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None

try:
    import openai as openai_module  # legacy SDK (<=0.x)
except ImportError:  # pragma: no cover
    openai_module = None

# Django imports
from django.conf import settings
from django.db import transaction

# Local imports
from grc.models import Framework
from grc.routes.Global.s3_fucntions import create_direct_mysql_client


logger = logging.getLogger(__name__)


class ChangeManagementService:
    """
    Service for handling change management of framework documents
    """
    
    def __init__(self):
        # Get data directory path
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # State file for tracking processed files
        self.state_file = self.data_dir / "state.json"
        self.processed_files_state = self.data_dir / "processed_files.json"
        
        # Initialize S3 client
        self.s3_client = create_direct_mysql_client()
        
        # Initialize OpenAI client if available
        self.openai_client = None
        self.legacy_openai = None
        self.openai_model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
        self.ai_enabled = bool(getattr(settings, "OPENAI_API_KEY", None)) and (
            OpenAI is not None or openai_module is not None
        )

        if self.ai_enabled:
            try:
                os.environ.setdefault("OPENAI_API_KEY", settings.OPENAI_API_KEY)
                if OpenAI is not None:
                    self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                    logger.info("OpenAI client initialized for ChangeManagementService.")
                else:
                    openai_module.api_key = settings.OPENAI_API_KEY
                    self.legacy_openai = openai_module
                    logger.info("Legacy OpenAI SDK configured for ChangeManagementService.")
            except Exception as exc:  # pragma: no cover
                logger.warning("Failed to initialize OpenAI client: %s", exc)
                self.ai_enabled = False
                self.openai_client = None
                self.legacy_openai = None
        else:
            if OpenAI is None and openai_module is None:
                logger.info("OpenAI package not installed; AI-assisted processing disabled.")
            elif not getattr(settings, "OPENAI_API_KEY", None):
                logger.info("OpenAI API key not configured; AI-assisted processing disabled.")

        # Supported file formats
        self.supported_formats = ['.pdf', '.PDF']
        
    def load_state(self) -> Dict:
        """Load state from state.json"""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except Exception as e:
                print(f"Error loading state: {e}")
                return {}
        return {}
    
    def load_processed_files(self) -> Dict:
        """Load list of already processed files"""
        if self.processed_files_state.exists():
            try:
                return json.loads(self.processed_files_state.read_text())
            except Exception as e:
                print(f"Error loading processed files: {e}")
                return {"processed": []}
        return {"processed": []}
    
    def save_processed_files(self, data: Dict):
        """Save processed files state"""
        try:
            self.processed_files_state.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error saving processed files: {e}")
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def extract_pdf_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                metadata = {
                    'num_pages': len(pdf_reader.pages),
                    'title': None,
                    'author': None,
                    'subject': None,
                    'creator': None,
                    'producer': None,
                    'creation_date': None,
                    'modification_date': None,
                }
                
                # Extract PDF metadata if available
                if pdf_reader.metadata:
                    metadata['title'] = pdf_reader.metadata.get('/Title', None)
                    metadata['author'] = pdf_reader.metadata.get('/Author', None)
                    metadata['subject'] = pdf_reader.metadata.get('/Subject', None)
                    metadata['creator'] = pdf_reader.metadata.get('/Creator', None)
                    metadata['producer'] = pdf_reader.metadata.get('/Producer', None)
                    metadata['creation_date'] = str(pdf_reader.metadata.get('/CreationDate', None))
                    metadata['modification_date'] = str(pdf_reader.metadata.get('/ModDate', None))
                
                # Extract first page text as sample
                if len(pdf_reader.pages) > 0:
                    first_page = pdf_reader.pages[0]
                    text = first_page.extract_text()
                    metadata['first_page_preview'] = text[:500] if text else None
                
                return metadata
                
        except Exception as e:
            print(f"Error extracting PDF metadata: {e}")
            return {'error': str(e)}
    
    def extract_amendment_info(self, file_path: Path, framework_name: str, ai_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extract amendment information from PDF
        This is a placeholder - you can enhance this with AI/NLP to extract actual changes
        """
        pdf_metadata = self.extract_pdf_metadata(file_path)
        
        amendment_info = {
            'amendment_name': f"{framework_name} - Update {datetime.now().strftime('%Y-%m-%d')}",
            'modified_sections': self._detect_modified_sections(file_path, pdf_metadata, ai_analysis),
            'content_summary': self._generate_content_summary(file_path, pdf_metadata, ai_analysis),
            'file_metadata': pdf_metadata,
            'detected_date': datetime.now().isoformat(),
            'ai_analysis': ai_analysis,
        }
        
        return amendment_info
    
    def _detect_modified_sections(self, file_path: Path, pdf_metadata: Dict, ai_analysis: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        Detect which sections were modified using the new structured AI response format
        """
        modified_sections: List[Dict[str, Any]] = []

        if ai_analysis:
            # Process modified_controls from AI analysis
            modified_controls = ai_analysis.get('modified_controls') or []
            if isinstance(modified_controls, list):
                for control in modified_controls:
                    if not isinstance(control, dict):
                        continue
                    
                    control_id = control.get('control_id', '')
                    control_name = control.get('control_name', 'Unnamed Control')
                    change_type = control.get('change_type', 'modified')
                    change_desc = control.get('change_description', '')
                    enhancements = control.get('enhancements') or []
                    related_controls = control.get('related_controls') or []
                    sub_policies = control.get('sub_policies') or []
                    
                    # If control has sub-policies, create entries for each
                    if sub_policies and isinstance(sub_policies, list):
                        for sub_policy in sub_policies:
                            if not isinstance(sub_policy, dict):
                                continue
                            modified_sections.append({
                                'section_type': 'sub_policy',
                                'control_id': control_id,
                                'policy_name': control_name,
                                'sub_policy_name': sub_policy.get('sub_policy_name', 'Unnamed Sub-policy'),
                                'modification_type': sub_policy.get('change_type', 'modified'),
                                'change_description': sub_policy.get('change_description', ''),
                                'requirements': sub_policy.get('requirements') or [],
                                'enhancements': enhancements,
                                'related_controls': related_controls
                            })
                    else:
                        # Control-level change without sub-policies
                        modified_sections.append({
                            'section_type': 'control',
                            'control_id': control_id,
                            'control_name': control_name,
                            'modification_type': change_type,
                            'change_description': change_desc,
                            'enhancements': enhancements,
                            'related_controls': related_controls
                        })
            
            # Process new_additions from AI analysis
            new_additions = ai_analysis.get('new_additions') or []
            if isinstance(new_additions, list):
                for addition in new_additions:
                    if not isinstance(addition, dict):
                        continue
                    modified_sections.append({
                        'section_type': 'new_control',
                        'control_id': addition.get('control_id', ''),
                        'control_name': addition.get('control_name', 'New Control'),
                        'modification_type': 'new',
                        'scope': addition.get('scope', ''),
                        'purpose': addition.get('purpose', ''),
                        'requirements': addition.get('requirements') or []
                    })
            
            # Process framework_references from AI analysis
            framework_refs = ai_analysis.get('framework_references') or []
            if isinstance(framework_refs, list):
                for ref in framework_refs:
                    if not isinstance(ref, dict):
                        continue
                    modified_sections.append({
                        'section_type': 'framework_reference',
                        'referenced_framework': ref.get('referenced_framework', ''),
                        'reference_type': ref.get('reference_type', 'mapping'),
                        'description': ref.get('description', '')
                    })

        if modified_sections:
            return modified_sections
        
        # Check if we can determine the framework type from filename
        filename = file_path.name.lower()
        
        if 'sp800-53' in filename or 'nist' in filename:
            modified_sections.append({
                'section_type': 'policy',
                'section_name': 'NIST SP 800-53 Controls',
                'modification_type': 'update',
                'description': 'Framework controls updated'
            })
        elif 'pci' in filename:
            modified_sections.append({
                'section_type': 'policy',
                'section_name': 'PCI DSS Requirements',
                'modification_type': 'update',
                'description': 'Payment Card Industry standards updated'
            })
        elif 'iso' in filename:
            modified_sections.append({
                'section_type': 'policy',
                'section_name': 'ISO Standards',
                'modification_type': 'update',
                'description': 'ISO framework standards updated'
            })
        else:
            # Generic modification entry
            modified_sections.append({
                'section_type': 'policy',
                'section_name': 'Framework Documentation',
                'modification_type': 'update',
                'description': 'Framework documentation updated'
            })
        
        return modified_sections
    
    def _generate_content_summary(self, file_path: Path, pdf_metadata: Dict, ai_analysis: Optional[Dict[str, Any]] = None) -> str:
        """Generate a summary of the content changes"""
        summary_parts = []
        
        # Add file information
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        summary_parts.append(f"Document size: {file_size_mb:.2f} MB")
        
        # Add page count
        if pdf_metadata.get('num_pages'):
            summary_parts.append(f"Total pages: {pdf_metadata['num_pages']}")
        
        # Add title if available
        if pdf_metadata.get('title'):
            summary_parts.append(f"Title: {pdf_metadata['title']}")
        
        # Add preview if available
        if pdf_metadata.get('first_page_preview'):
            summary_parts.append(f"Preview: {pdf_metadata['first_page_preview'][:200]}...")
        
        if ai_analysis:
            ai_summary = ai_analysis.get('summary') or ai_analysis.get('rationale')
            if ai_summary:
                summary_parts.append(f"AI insight: {ai_summary[:200]}...")
            if ai_analysis.get('framework_name'):
                summary_parts.append(f"AI framework: {ai_analysis['framework_name']}")
            
            # Summarize modified controls
            modified_controls = ai_analysis.get('modified_controls') or []
            if isinstance(modified_controls, list) and modified_controls:
                control_count = len(modified_controls)
                summary_parts.append(f"Modified controls: {control_count}")
            
            # Summarize new additions
            new_additions = ai_analysis.get('new_additions') or []
            if isinstance(new_additions, list) and new_additions:
                new_count = len(new_additions)
                summary_parts.append(f"New controls: {new_count}")
        
        return " | ".join(summary_parts)
    
    def _extract_pdf_text_snippet(self, file_path: Path, max_pages: int = 5, max_chars: int = 6000) -> Optional[str]:
        """Extract a limited text sample from the PDF for AI processing."""
        try:
            snippets: List[str] = []
            total_chars = 0
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                page_count = min(len(reader.pages), max_pages)
                for page_index in range(page_count):
                    page = reader.pages[page_index]
                    text = page.extract_text()
                    if not text:
                        continue
                    cleaned = " ".join(text.split())
                    if not cleaned:
                        continue
                    remaining = max_chars - total_chars
                    if remaining <= 0:
                        break
                    snippet_piece = cleaned[:remaining]
                    snippets.append(snippet_piece)
                    total_chars += len(snippet_piece)
                    if total_chars >= max_chars:
                        break
            return " ".join(snippets) if snippets else None
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to extract text snippet from %s: %s", file_path.name, exc)
            return None
    
    def analyze_pdf_with_ai(self, file_path: Path, framework_hint: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Use OpenAI to infer framework, policies, and structural information from the PDF.
        """
        if not self.ai_enabled or not self.openai_client:
            return None
        
        snippet = self._extract_pdf_text_snippet(file_path)
        if not snippet:
            logger.info("AI analysis skipped for %s - no text extracted.", file_path.name)
            return None
        
        user_prompt_text = (
            "You are given a document detailing changes or updates in a security or regulatory framework. "
            "Your task is to extract the following key elements based on the framework modifications:\n\n"
            
            "1. **Modified Controls or Policies:**\n"
            "   - List the names of any modified policies or controls.\n"
            "   - Specify if it is a new control or a modified one.\n"
            "   - Provide details of the control enhancements or updates that have been made.\n"
            "   - For each modified control or policy, specify if there are any sub-policies involved.\n\n"
            
            "2. **Sub-policy Changes:**\n"
            "   - If a sub-policy was modified, provide the policy name and the sub-policy name.\n"
            "   - For each sub-policy, mention the specific modifications or enhancements.\n\n"
            
            "3. **New Additions:**\n"
            "   - Identify any new controls or sub-policies that have been added.\n"
            "   - For each new addition, provide details of its scope and purpose.\n\n"
            
            "4. **Control Enhancements and Revisions:**\n"
            "   - Describe any enhancements or revisions to existing controls, including the specific updates to control requirements or implementation examples.\n"
            "   - For each updated control, list any associated related controls or references (if provided).\n\n"
            
            "5. **Other Changes:**\n"
            "   - Identify if there are new references to other frameworks, standards, or controls.\n"
            "   - If there is any related policy or procedure added or revised, mention it.\n\n"
            
            "**Output Format:**\n"
            "Respond strictly as valid JSON with these top-level keys:\n"
            "{\n"
            "  \"framework_name\": \"string (name of the framework, e.g., NIST SP 800-53, Basel III, PCI DSS)\",\n"
            "  \"probable_aliases\": [\"array of alternative names for the framework\"],\n"
            "  \"confidence\": 0.0-1.0,\n"
            "  \"summary\": \"Brief overview of all changes in this document\",\n"
            "  \"modified_controls\": [\n"
            "    {\n"
            "      \"control_id\": \"Control identifier (e.g., AC-2, SI-7)\",\n"
            "      \"control_name\": \"Full name of the control or policy\",\n"
            "      \"change_type\": \"new | modified | enhanced | deprecated\",\n"
            "      \"change_description\": \"Detailed description of what changed\",\n"
            "      \"enhancements\": [\"List of specific enhancements or updates\"],\n"
            "      \"related_controls\": [\"List of related control IDs if mentioned\"],\n"
            "      \"sub_policies\": [\n"
            "        {\n"
            "          \"sub_policy_name\": \"Name of sub-policy\",\n"
            "          \"change_type\": \"new | modified | enhanced | deprecated\",\n"
            "          \"change_description\": \"What changed in this sub-policy\",\n"
            "          \"requirements\": [\"Specific requirements or implementation details\"]\n"
            "        }\n"
            "      ]\n"
            "    }\n"
            "  ],\n"
            "  \"new_additions\": [\n"
            "    {\n"
            "      \"control_id\": \"New control identifier\",\n"
            "      \"control_name\": \"Name of new control/policy\",\n"
            "      \"scope\": \"Description of scope\",\n"
            "      \"purpose\": \"Purpose and rationale for addition\",\n"
            "      \"requirements\": [\"Implementation requirements\"]\n"
            "    }\n"
            "  ],\n"
            "  \"framework_references\": [\n"
            "    {\n"
            "      \"referenced_framework\": \"Name of referenced standard/framework\",\n"
            "      \"reference_type\": \"mapping | alignment | compliance\",\n"
            "      \"description\": \"How it relates to this framework\"\n"
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Do not include any explanatory text outside the JSON. Extract all available information from the document."
        )
        if framework_hint:
            user_prompt_text += f" Use this hint about the framework: {framework_hint}. "
        user_prompt_text += f"\n\nText excerpt:\n{snippet}"
        
        system_message = {
            "role": "system",
            "content": "You are a precise regulatory intelligence assistant that always answers with valid JSON."
        }
        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_prompt_text
                }
            ],
        }
        
        try:
            ai_text: Optional[str] = None

            if self.openai_client:
                if hasattr(self.openai_client, "responses"):
                    response = self.openai_client.responses.create(
                        model=self.openai_model,
                        input=[system_message, user_message],
                        temperature=0.1,
                    )
                    ai_text = getattr(response, "output_text", None)
                    if not ai_text:
                        try:
                            segments = []
                            for item in getattr(response, "output", []) or []:
                                for content in item.get("content", []):
                                    if content.get("type") == "text" and content.get("text"):
                                        segments.append(content["text"])
                            ai_text = " ".join(segments).strip() if segments else None
                        except Exception:  # pragma: no cover
                            ai_text = None
                elif hasattr(self.openai_client, "chat"):
                    response = self.openai_client.chat.completions.create(
                        model=self.openai_model,
                        messages=[system_message, {"role": "user", "content": user_prompt_text}],
                        temperature=0.1,
                    )
                    if response and response.choices:
                        ai_text = response.choices[0].message.content

            if not ai_text and self.legacy_openai:
                response = self.legacy_openai.ChatCompletion.create(
                    model=self.openai_model,
                    messages=[system_message, {"role": "user", "content": user_prompt_text}],
                    temperature=0.1,
                )
                if response and response.get("choices"):
                    ai_text = response["choices"][0]["message"]["content"]

            if not ai_text:
                logger.warning("OpenAI response did not contain text for %s", file_path.name)
                return None

            ai_text = ai_text.strip()
            # Handle common markdown code fences (```json ... ```)
            if ai_text.startswith("```"):
                fence_removed = ai_text[3:]
                # If language identifier is present (e.g., json, JSON)
                if fence_removed.lstrip().lower().startswith("json"):
                    fence_removed = fence_removed.lstrip()[4:]
                ai_text = fence_removed
                if ai_text.endswith("```"):
                    ai_text = ai_text[:-3]
                ai_text = ai_text.strip()

            try:
                analysis = json.loads(ai_text)
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI JSON for %s. Response: %s", file_path.name, ai_text)
                return None
            
            policies = analysis.get('policies')
            if isinstance(policies, dict):
                analysis['policies'] = list(policies.values())
            elif policies is None:
                analysis['policies'] = []
            elif not isinstance(policies, list):
                analysis['policies'] = []

            probable_aliases = analysis.get('probable_aliases')
            if probable_aliases is None:
                analysis['probable_aliases'] = []
            elif not isinstance(probable_aliases, list):
                analysis['probable_aliases'] = [str(probable_aliases)]
            
            return analysis
        
        except Exception as exc:  # pragma: no cover
            logger.warning("OpenAI analysis failed for %s: %s", file_path.name, exc)
            return None
    
    def upload_to_s3(self, file_path: Path, user_id: str = "system") -> Dict:
        """
        Upload PDF to S3 bucket using the same filename
        """
        try:
            print(f"📤 Uploading {file_path.name} to S3...")
            
            # Use original filename for S3 upload
            original_filename = file_path.name
            
            # Upload to S3 with 'changemanagement' module
            result = self.s3_client.upload(
                file_path=str(file_path),
                user_id=user_id,
                custom_file_name=original_filename,
                module='changemanagement'
            )
            
            if result.get('success'):
                print(f"✅ Successfully uploaded to S3: {result['file_info']['url']}")
                return {
                    'success': True,
                    's3_url': result['file_info']['url'],
                    's3_key': result['file_info']['s3Key'],
                    'stored_name': result['file_info']['storedName'],
                    'file_size': result['file_info']['size']
                }
            else:
                print(f"❌ Failed to upload to S3: {result.get('error')}")
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error')
                }
                
        except Exception as e:
            print(f"❌ Exception during S3 upload: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def identify_framework(self, file_path: Path, ai_analysis: Optional[Dict[str, Any]] = None) -> Optional[Framework]:
        """
        Identify which framework this file belongs to based on filename
        """
        filename = file_path.name.lower()
        
        # Map filename patterns to framework names
        framework_patterns = {
            'sp800-53': ['NIST SP 800-53', 'NIST 800-53', 'SP800-53'],
            'sp800': ['NIST SP 800-53', 'NIST 800-53', 'SP800-53'],
            'nist': ['NIST SP 800-53', 'NIST 800-53', 'SP800-53'],
            'pci': ['PCI DSS', 'PCI-DSS', 'Payment Card Industry'],
            'iso27001': ['ISO 27001', 'ISO/IEC 27001'],
            'iso': ['ISO 27001', 'ISO/IEC 27001'],
            'hipaa': ['HIPAA'],
            'gdpr': ['GDPR'],
            'sox': ['SOX', 'Sarbanes-Oxley'],
        }
        
        frameworks_queryset = Framework.objects.all()
        try:
            frameworks = list(frameworks_queryset)
        except Exception as exc:
            logger.warning("Unable to fetch frameworks from database: %s", exc)
            frameworks = []

        # Try to match filename with framework patterns
        for pattern, possible_names in framework_patterns.items():
            if pattern in filename:
                # Try to find framework with any of the possible names
                for framework_name in possible_names:
                    framework = Framework.objects.filter(
                        FrameworkName__icontains=framework_name
                    ).first()
                    
                    if framework:
                        print(f"✅ Identified framework: {framework.FrameworkName} (ID: {framework.FrameworkId})")
                        return framework
        
        # AI-assisted matching based on analysis output
        ai_candidates: List[str] = []
        if ai_analysis:
            primary = ai_analysis.get('framework_name')
            if isinstance(primary, str) and primary.strip():
                ai_candidates.append(primary.strip())
            aliases = ai_analysis.get('probable_aliases') or []
            if isinstance(aliases, list):
                ai_candidates.extend([alias.strip() for alias in aliases if isinstance(alias, str) and alias.strip()])
        
        if ai_candidates:
            framework_names = [fw.FrameworkName for fw in frameworks]
            
            for candidate in ai_candidates:
                if not candidate:
                    continue
                
                direct_match = Framework.objects.filter(
                    FrameworkName__icontains=candidate
                ).first()
                if direct_match:
                    print(f"✅ AI-identified framework: {direct_match.FrameworkName} (ID: {direct_match.FrameworkId})")
                    return direct_match
                
                close_matches = get_close_matches(candidate, framework_names, n=1, cutoff=0.7)
                if close_matches:
                    matched_name = close_matches[0]
                    framework = next((fw for fw in frameworks if fw.FrameworkName == matched_name), None)
                    if framework:
                        print(f"✅ AI-suggested framework matched: {framework.FrameworkName} (ID: {framework.FrameworkId})")
                        return framework
        
        # Fallback: use filename to fuzzy match against known frameworks
        normalized_filename = re.sub(r'[^a-z0-9]+', ' ', Path(file_path).stem.lower()).strip()
        if normalized_filename and frameworks:
            for framework in frameworks:
                normalized_fw = re.sub(r'[^a-z0-9]+', ' ', framework.FrameworkName.lower()).strip()
                if normalized_fw and (
                    normalized_fw in normalized_filename or normalized_filename in normalized_fw
                ):
                    print(f"✅ Filename matched framework: {framework.FrameworkName} (ID: {framework.FrameworkId})")
                    return framework
            
            normalized_fw_names = [re.sub(r'[^a-z0-9]+', ' ', fw.FrameworkName.lower()).strip() for fw in frameworks]
            matches = get_close_matches(normalized_filename, normalized_fw_names, n=1, cutoff=0.65)
            if matches:
                matched_name = matches[0]
                for framework in frameworks:
                    normalized_fw = re.sub(r'[^a-z0-9]+', ' ', framework.FrameworkName.lower()).strip()
                    if normalized_fw == matched_name:
                        print(f"✅ Filename fuzzy matched framework: {framework.FrameworkName} (ID: {framework.FrameworkId})")
                        return framework
        
        # If no specific match, log and return None
        print(f"⚠️ Could not identify framework for file: {file_path.name}")
        return None
    
    def update_framework_amendment(self, framework: Framework, amendment_data: Dict, s3_info: Dict):
        """
        Update the framework's Amendment column with new amendment information
        """
        try:
            with transaction.atomic():
                # Load existing amendments
                existing_amendments = framework.Amendment if framework.Amendment else []
                
                if not isinstance(existing_amendments, list):
                    existing_amendments = []
                
                # Create new amendment entry
                new_amendment = {
                    'amendment_id': len(existing_amendments) + 1,
                    'amendment_name': amendment_data['amendment_name'],
                    'modified_sections': amendment_data['modified_sections'],
                    'content_summary': amendment_data['content_summary'],
                    's3_url': s3_info['s3_url'],
                    's3_key': s3_info['s3_key'],
                    'stored_name': s3_info['stored_name'],
                    'file_size': s3_info['file_size'],
                    'uploaded_date': datetime.now().isoformat(),
                    'file_metadata': amendment_data.get('file_metadata', {}),
                    'ai_analysis': amendment_data.get('ai_analysis', {}),
                }
                
                # Append new amendment
                existing_amendments.append(new_amendment)
                
                # Update framework
                framework.Amendment = existing_amendments
                framework.save()
                
                print(f"✅ Successfully updated framework {framework.FrameworkName} with new amendment")
                return True
                
        except Exception as e:
            print(f"❌ Error updating framework amendment: {str(e)}")
            return False
    
    def process_pdf_file(self, file_path: Path, user_id: str = "system") -> Dict:
        """
        Process a single PDF file:
        1. Upload to S3
        2. Extract amendment info
        3. Update framework Amendment column
        """
        print(f"\n{'='*60}")
        print(f"📄 Processing file: {file_path.name}")
        print(f"{'='*60}")
        
        result = {
            'success': False,
            'file_name': file_path.name,
            'file_path': str(file_path),
            'timestamp': datetime.now().isoformat(),
        }
        
        try:
            # 1. Calculate file hash
            file_hash = self.calculate_file_hash(file_path)
            result['file_hash'] = file_hash
            
            # 2. Check if already processed
            processed_files = self.load_processed_files()
            if file_hash in processed_files.get('processed', []):
                print(f"⏭️ File already processed (hash: {file_hash[:16]}...)")
                result['status'] = 'already_processed'
                result['success'] = True
                return result
            
            # 3. Optional AI analysis based on PDF content
            ai_analysis = self.analyze_pdf_with_ai(file_path)
            if ai_analysis:
                result['ai_analysis'] = ai_analysis
            
            # 4. Identify framework (using AI hints if available)
            framework = self.identify_framework(file_path, ai_analysis)
            if not framework:
                result['error'] = 'Could not identify framework'
                result['status'] = 'framework_not_found'
                print(f"⚠️ Skipping file - framework not identified")
                return result
            
            result['framework_id'] = framework.FrameworkId
            result['framework_name'] = framework.FrameworkName
            
            # 5. Upload to S3
            s3_result = self.upload_to_s3(file_path, user_id)
            if not s3_result.get('success'):
                result['error'] = f"S3 upload failed: {s3_result.get('error')}"
                result['status'] = 's3_upload_failed'
                return result
            
            result['s3_url'] = s3_result['s3_url']
            result['s3_key'] = s3_result['s3_key']
            
            # 6. Extract amendment information
            amendment_info = self.extract_amendment_info(file_path, framework.FrameworkName, ai_analysis)
            result['amendment_info'] = amendment_info
            
            # 7. Update framework Amendment column
            update_success = self.update_framework_amendment(framework, amendment_info, s3_result)
            
            if update_success:
                # 8. Mark as processed
                processed_files['processed'].append(file_hash)
                self.save_processed_files(processed_files)
                
                result['success'] = True
                result['status'] = 'completed'
                print(f"✅ Successfully processed {file_path.name}")
            else:
                result['error'] = 'Failed to update framework amendment'
                result['status'] = 'amendment_update_failed'
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            result['status'] = 'exception'
            print(f"❌ Exception processing file: {str(e)}")
            import traceback
            traceback.print_exc()
            return result
    
    def scan_and_process_pdfs(self, user_id: str = "system") -> Dict:
        """
        Scan data directory for PDF files and process them
        """
        print(f"\n{'='*60}")
        print(f"🔍 Scanning for PDFs in: {self.data_dir}")
        print(f"{'='*60}\n")
        
        results = {
            'scan_time': datetime.now().isoformat(),
            'directory': str(self.data_dir),
            'files_found': 0,
            'files_processed': 0,
            'files_skipped': 0,
            'files_failed': 0,
            'processed_files': [],
            'errors': [],
        }
        
        try:
            # Find all PDF files in data directory
            pdf_files = []
            for ext in self.supported_formats:
                pdf_files.extend(list(self.data_dir.glob(f"*{ext}")))
            
            results['files_found'] = len(pdf_files)
            
            if not pdf_files:
                print("⚠️ No PDF files found in data directory")
                return results
            
            print(f"📁 Found {len(pdf_files)} PDF file(s)")
            
            # Process each PDF file
            for pdf_file in pdf_files:
                print(f"\n🔄 Processing: {pdf_file.name}")
                
                process_result = self.process_pdf_file(pdf_file, user_id)
                results['processed_files'].append(process_result)
                
                if process_result['success']:
                    if process_result.get('status') == 'already_processed':
                        results['files_skipped'] += 1
                    else:
                        results['files_processed'] += 1
                else:
                    results['files_failed'] += 1
                    results['errors'].append({
                        'file': pdf_file.name,
                        'error': process_result.get('error', 'Unknown error')
                    })
            
            # Summary
            print(f"\n{'='*60}")
            print(f"📊 PROCESSING SUMMARY")
            print(f"{'='*60}")
            print(f"✅ Successfully processed: {results['files_processed']}")
            print(f"⏭️ Skipped (already processed): {results['files_skipped']}")
            print(f"❌ Failed: {results['files_failed']}")
            print(f"{'='*60}\n")
            
            return results
            
        except Exception as e:
            results['error'] = str(e)
            print(f"❌ Error during scan: {str(e)}")
            import traceback
            traceback.print_exc()
            return results


# Singleton instance
_change_management_service = None

def get_change_management_service() -> ChangeManagementService:
    """Get or create singleton instance of ChangeManagementService"""
    global _change_management_service
    if _change_management_service is None:
        _change_management_service = ChangeManagementService()
    return _change_management_service


# Convenience functions for API endpoints
def scan_and_process_changes(user_id: str = "system") -> Dict:
    """Scan data directory and process any new PDF files"""
    service = get_change_management_service()
    return service.scan_and_process_pdfs(user_id)


def process_specific_file(file_name: str, user_id: str = "system") -> Dict:
    """Process a specific PDF file by name"""
    service = get_change_management_service()
    file_path = service.data_dir / file_name
    
    if not file_path.exists():
        return {
            'success': False,
            'error': f'File not found: {file_name}'
        }
    
    return service.process_pdf_file(file_path, user_id)


def get_framework_amendments(framework_id: int) -> Dict:
    """Get all amendments for a specific framework"""
    try:
        framework = Framework.objects.get(FrameworkId=framework_id)
        return {
            'success': True,
            'framework_id': framework.FrameworkId,
            'framework_name': framework.FrameworkName,
            'amendments': framework.Amendment if framework.Amendment else []
        }
    except Framework.DoesNotExist:
        return {
            'success': False,
            'error': f'Framework not found: {framework_id}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# ========================================================================
# API VIEW FUNCTIONS FOR DJANGO URLS
# ========================================================================

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json as json_module


@csrf_exempt
@require_http_methods(["POST", "GET"])
def scan_changes(request):
    """
    API endpoint to scan and process PDF files from data directory
    POST: Trigger a scan and process operation
    GET: Get the last scan results
    """
    try:
        # Get user_id from request
        user_id = "system"
        if request.method == "POST":
            try:
                body = json_module.loads(request.body) if request.body else {}
                user_id = body.get('user_id', 'system')
            except:
                pass
        elif request.user and hasattr(request.user, 'UserId'):
            user_id = str(request.user.UserId)
        
        # Run the scan
        result = scan_and_process_changes(user_id)
        
        return JsonResponse({
            'success': True,
            'data': result,
            'message': f'Scan completed. Processed: {result.get("files_processed", 0)}, Skipped: {result.get("files_skipped", 0)}, Failed: {result.get("files_failed", 0)}'
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def process_file(request, file_name):
    """
    API endpoint to process a specific PDF file
    """
    try:
        # Get user_id from request
        user_id = "system"
        if request.body:
            try:
                body = json_module.loads(request.body)
                user_id = body.get('user_id', 'system')
            except:
                pass
        elif request.user and hasattr(request.user, 'UserId'):
            user_id = str(request.user.UserId)
        
        # Process the file
        result = process_specific_file(file_name, user_id)
        
        if result.get('success'):
            return JsonResponse({
                'success': True,
                'data': result,
                'message': f'Successfully processed {file_name}'
            }, status=200)
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'data': result
            }, status=400)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_amendments(request, framework_id):
    """
    API endpoint to get all amendments for a specific framework
    """
    try:
        result = get_framework_amendments(framework_id)
        
        if result.get('success'):
            return JsonResponse({
                'success': True,
                'data': result,
                'message': f'Retrieved amendments for framework {framework_id}'
            }, status=200)
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_status(request):
    """
    API endpoint to get change management system status
    """
    try:
        service = get_change_management_service()
        
        # Get processed files state
        processed_files = service.load_processed_files()
        
        # Count PDF files in directory
        pdf_files = []
        for ext in service.supported_formats:
            pdf_files.extend(list(service.data_dir.glob(f"*{ext}")))
        
        status = {
            'service_status': 'operational',
            'data_directory': str(service.data_dir),
            'pdf_files_count': len(pdf_files),
            'processed_files_count': len(processed_files.get('processed', [])),
            's3_configured': service.s3_client is not None,
            'supported_formats': service.supported_formats,
        }
        
        return JsonResponse({
            'success': True,
            'data': status,
            'message': 'Change management system is operational'
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'service_status': 'error'
        }, status=500)


if __name__ == "__main__":
    # Test the service
    print("🚀 Testing Change Management Service")
    result = scan_and_process_changes()
    print(f"\n📋 Results:")
    print(json.dumps(result, indent=2, default=str))

