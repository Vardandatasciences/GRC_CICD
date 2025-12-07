"""
AI-Powered Similarity Matcher for Framework Comparison
Matches modified controls (target) with original policies/sub-policies/compliances (origin)
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from difflib import SequenceMatcher
import re

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import openai as openai_module
except ImportError:
    openai_module = None

from django.conf import settings

logger = logging.getLogger(__name__)


class SimilarityMatcher:
    """
    Service for matching target controls with origin policies using AI and text similarity
    """
    
    def __init__(self):
        self.openai_client = None
        self.legacy_openai = None
        self.openai_model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
        self.embedding_model = getattr(settings, "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.ai_enabled = bool(getattr(settings, "OPENAI_API_KEY", None)) and (
            OpenAI is not None or openai_module is not None
        )
        
        if self.ai_enabled:
            try:
                if OpenAI is not None:
                    self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                    logger.info("OpenAI client initialized for SimilarityMatcher")
                else:
                    openai_module.api_key = settings.OPENAI_API_KEY
                    self.legacy_openai = openai_module
                    logger.info("Legacy OpenAI SDK configured for SimilarityMatcher")
            except Exception as exc:
                logger.warning("Failed to initialize OpenAI client: %s", exc)
                self.ai_enabled = False
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple text similarity using SequenceMatcher (0.0 - 1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        # Normalize text
        text1_normalized = text1.lower().strip()
        text2_normalized = text2.lower().strip()
        
        # Calculate similarity ratio
        return SequenceMatcher(None, text1_normalized, text2_normalized).ratio()
    
    def calculate_keyword_overlap(self, text1: str, text2: str) -> float:
        """
        Calculate keyword overlap score (0.0 - 1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        # Extract keywords (words with 4+ characters, excluding common words)
        stop_words = {
            'that', 'this', 'with', 'from', 'have', 'been', 'were', 'will',
            'shall', 'must', 'should', 'would', 'could', 'their', 'there',
            'which', 'where', 'when', 'what', 'about', 'such', 'into', 'only'
        }
        
        def extract_keywords(text):
            words = re.findall(r'\b[a-z]{4,}\b', text.lower())
            return set(w for w in words if w not in stop_words)
        
        keywords1 = extract_keywords(text1)
        keywords2 = extract_keywords(text2)
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_id_similarity(self, target_id: str, origin_id: str) -> float:
        """
        Calculate similarity between control/policy IDs
        Returns higher score for matching patterns (e.g., "1.2.3" vs "Requirement 1.2.3")
        """
        if not target_id or not origin_id:
            return 0.0
        
        # Extract numeric patterns
        target_nums = re.findall(r'\d+\.?\d*', target_id)
        origin_nums = re.findall(r'\d+\.?\d*', origin_id)
        
        if target_nums and origin_nums:
            # Check if any numbers match
            for t_num in target_nums:
                for o_num in origin_nums:
                    if t_num == o_num or t_num in o_num or o_num in t_num:
                        return 0.9  # High score for ID match
        
        # Fallback to text similarity
        return self.calculate_text_similarity(target_id, origin_id) * 0.7
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get OpenAI embedding for text
        """
        if not self.ai_enabled or not text:
            return None
        
        try:
            if self.openai_client:
                response = self.openai_client.embeddings.create(
                    model=self.embedding_model,
                    input=text[:8000]  # Limit text length
                )
                return response.data[0].embedding
            elif self.legacy_openai:
                response = self.legacy_openai.Embedding.create(
                    model=self.embedding_model,
                    input=text[:8000]
                )
                return response['data'][0]['embedding']
        except Exception as e:
            logger.warning("Failed to get embedding: %s", str(e))
            return None
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def calculate_hybrid_similarity(
        self,
        target_control: Dict[str, Any],
        origin_item: Dict[str, Any],
        item_type: str
    ) -> float:
        """
        Calculate hybrid similarity score combining multiple methods
        
        Args:
            target_control: Modified control from target
            origin_item: Policy/SubPolicy/Compliance from origin
            item_type: 'policy', 'subpolicy', or 'compliance'
        
        Returns:
            Similarity score (0.0 - 1.0)
        """
        scores = []
        weights = []
        
        # 1. ID similarity (high weight)
        target_id = target_control.get('control_id', '')
        if item_type == 'policy':
            origin_id = origin_item.get('Identifier', '')
        elif item_type == 'subpolicy':
            origin_id = origin_item.get('Identifier', '')
        else:  # compliance
            origin_id = origin_item.get('ComplianceTitle', '')
        
        if target_id and origin_id:
            id_score = self.calculate_id_similarity(target_id, origin_id)
            scores.append(id_score)
            weights.append(3.0)  # High weight for ID match
        
        # 2. Name/Title similarity
        target_name = target_control.get('control_name', '')
        if item_type == 'policy':
            origin_name = origin_item.get('PolicyName', '')
        elif item_type == 'subpolicy':
            origin_name = origin_item.get('SubPolicyName', '')
        else:
            origin_name = origin_item.get('ComplianceTitle', '')
        
        if target_name and origin_name:
            name_score = self.calculate_text_similarity(target_name, origin_name)
            scores.append(name_score)
            weights.append(2.0)  # Medium-high weight
        
        # 3. Description similarity
        target_desc = target_control.get('change_description', '')
        if item_type == 'policy':
            origin_desc = origin_item.get('PolicyDescription', '')
        elif item_type == 'subpolicy':
            origin_desc = origin_item.get('Description', '')
        else:
            origin_desc = origin_item.get('ComplianceItemDescription', '')
        
        if target_desc and origin_desc:
            desc_score = self.calculate_text_similarity(target_desc, origin_desc)
            scores.append(desc_score)
            weights.append(1.5)  # Medium weight
        
        # 4. Keyword overlap
        combined_target = f"{target_name} {target_desc}"
        combined_origin = f"{origin_name} {origin_desc}"
        
        if combined_target.strip() and combined_origin.strip():
            keyword_score = self.calculate_keyword_overlap(combined_target, combined_origin)
            scores.append(keyword_score)
            weights.append(1.0)  # Lower weight
        
        # Calculate weighted average
        if not scores:
            return 0.0
        
        weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
        total_weight = sum(weights)
        
        return weighted_sum / total_weight
    
    def calculate_ai_similarity(
        self,
        target_control: Dict[str, Any],
        origin_item: Dict[str, Any],
        item_type: str
    ) -> float:
        """
        Calculate AI-based similarity using embeddings
        """
        if not self.ai_enabled:
            return 0.0
        
        # Prepare text for embedding
        target_text = f"{target_control.get('control_id', '')} {target_control.get('control_name', '')} {target_control.get('change_description', '')}"
        
        if item_type == 'policy':
            origin_text = f"{origin_item.get('Identifier', '')} {origin_item.get('PolicyName', '')} {origin_item.get('PolicyDescription', '')}"
        elif item_type == 'subpolicy':
            origin_text = f"{origin_item.get('Identifier', '')} {origin_item.get('SubPolicyName', '')} {origin_item.get('Description', '')}"
        else:
            origin_text = f"{origin_item.get('ComplianceTitle', '')} {origin_item.get('ComplianceItemDescription', '')}"
        
        # Get embeddings
        target_embedding = self.get_embedding(target_text)
        origin_embedding = self.get_embedding(origin_text)
        
        if target_embedding and origin_embedding:
            return self.cosine_similarity(target_embedding, origin_embedding)
        
        return 0.0
    
    def find_best_matches(
        self,
        target_control: Dict[str, Any],
        origin_data: Dict[str, Any],
        top_n: int = 5,
        use_ai: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Find best matching items in origin for a target control
        
        Args:
            target_control: Modified control from target
            origin_data: Complete origin framework data with policies
            top_n: Number of top matches to return
            use_ai: Whether to use AI embeddings (slower but more accurate)
        
        Returns:
            List of matches with scores and details
        """
        matches = []
        
        # Extract policies from origin data
        policies = origin_data.get('policies', [])
        
        for policy in policies:
            # Check policy level
            hybrid_score = self.calculate_hybrid_similarity(target_control, policy, 'policy')
            ai_score = 0.0
            
            if use_ai and self.ai_enabled:
                ai_score = self.calculate_ai_similarity(target_control, policy, 'policy')
            
            # Combine scores (weighted average)
            if use_ai and ai_score > 0:
                final_score = (hybrid_score * 0.6) + (ai_score * 0.4)
            else:
                final_score = hybrid_score
            
            matches.append({
                'type': 'policy',
                'item': policy,
                'policy_id': policy.get('PolicyId'),
                'policy_name': policy.get('PolicyName'),
                'identifier': policy.get('Identifier'),
                'score': final_score,
                'hybrid_score': hybrid_score,
                'ai_score': ai_score if use_ai else None,
                'path': f"Policy: {policy.get('PolicyName')}"
            })
            
            # Check sub-policy level
            for subpolicy in policy.get('subpolicies', []):
                hybrid_score = self.calculate_hybrid_similarity(target_control, subpolicy, 'subpolicy')
                ai_score = 0.0
                
                if use_ai and self.ai_enabled:
                    ai_score = self.calculate_ai_similarity(target_control, subpolicy, 'subpolicy')
                
                if use_ai and ai_score > 0:
                    final_score = (hybrid_score * 0.6) + (ai_score * 0.4)
                else:
                    final_score = hybrid_score
                
                matches.append({
                    'type': 'subpolicy',
                    'item': subpolicy,
                    'policy_id': policy.get('PolicyId'),
                    'policy_name': policy.get('PolicyName'),
                    'subpolicy_id': subpolicy.get('SubPolicyId'),
                    'subpolicy_name': subpolicy.get('SubPolicyName'),
                    'identifier': subpolicy.get('Identifier'),
                    'score': final_score,
                    'hybrid_score': hybrid_score,
                    'ai_score': ai_score if use_ai else None,
                    'path': f"Policy: {policy.get('PolicyName')} > Sub-Policy: {subpolicy.get('SubPolicyName')}"
                })
                
                # Check compliance level
                for compliance in subpolicy.get('compliances', []):
                    hybrid_score = self.calculate_hybrid_similarity(target_control, compliance, 'compliance')
                    ai_score = 0.0
                    
                    if use_ai and self.ai_enabled:
                        ai_score = self.calculate_ai_similarity(target_control, compliance, 'compliance')
                    
                    if use_ai and ai_score > 0:
                        final_score = (hybrid_score * 0.6) + (ai_score * 0.4)
                    else:
                        final_score = hybrid_score
                    
                    matches.append({
                        'type': 'compliance',
                        'item': compliance,
                        'policy_id': policy.get('PolicyId'),
                        'policy_name': policy.get('PolicyName'),
                        'subpolicy_id': subpolicy.get('SubPolicyId'),
                        'subpolicy_name': subpolicy.get('SubPolicyName'),
                        'compliance_id': compliance.get('ComplianceId'),
                        'compliance_title': compliance.get('ComplianceTitle'),
                        'score': final_score,
                        'hybrid_score': hybrid_score,
                        'ai_score': ai_score if use_ai else None,
                        'path': f"Policy: {policy.get('PolicyName')} > Sub-Policy: {subpolicy.get('SubPolicyName')} > Compliance: {compliance.get('ComplianceTitle')}"
                    })
        
        # Sort by score (descending) and return top N
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        return matches[:top_n]
    
    def batch_match_controls(
        self,
        target_controls: List[Dict[str, Any]],
        origin_data: Dict[str, Any],
        use_ai: bool = False
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Match multiple target controls to origin items
        
        Args:
            target_controls: List of modified controls
            origin_data: Complete origin framework data
            use_ai: Whether to use AI (slower but more accurate)
        
        Returns:
            Dictionary mapping control_id to list of matches
        """
        results = {}
        
        for control in target_controls:
            control_id = control.get('control_id', '')
            if not control_id:
                continue
            
            matches = self.find_best_matches(control, origin_data, top_n=3, use_ai=use_ai)
            results[control_id] = matches
        
        return results


# Singleton instance
_similarity_matcher = None

def get_similarity_matcher() -> SimilarityMatcher:
    """Get or create singleton instance of SimilarityMatcher"""
    global _similarity_matcher
    if _similarity_matcher is None:
        _similarity_matcher = SimilarityMatcher()
    return _similarity_matcher


