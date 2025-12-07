# AI-Powered Similarity Matching for Framework Comparison

## Overview

This feature implements AI-powered similarity matching to help users identify which origin policies/sub-policies/compliances correspond to modified controls in framework amendments.

## Architecture

```
Frontend (Vue)
    ↓
frameworkComparisonService.js
    ↓
Django REST API (framework_comparison.py)
    ↓
SimilarityMatcher Service (similarity_matcher.py)
    ↓
OpenAI Embeddings API (optional, for AI mode)
```

## Components

### 1. Backend Service: `similarity_matcher.py`

**Main Class:** `SimilarityMatcher`

**Key Methods:**

- `calculate_hybrid_similarity()` - Combines multiple similarity metrics:
  - ID similarity (control/requirement numbers)
  - Name/title similarity
  - Description similarity
  - Keyword overlap
  - Weighted scoring

- `calculate_ai_similarity()` - Uses OpenAI embeddings:
  - Generates embeddings for control text
  - Calculates cosine similarity
  - More accurate but slower and requires API key

- `find_best_matches()` - Main matching function:
  - Searches across all policies, sub-policies, and compliances
  - Returns top N matches sorted by score
  - Supports both hybrid and AI modes

- `batch_match_controls()` - Batch processing:
  - Matches multiple controls at once
  - Efficient for processing all amendments

### 2. API Endpoints: `framework_comparison.py`

#### POST `/framework-comparison/{framework_id}/find-matches/`

Find best matching origin items for a single target control.

**Request:**
```json
{
  "control": {
    "control_id": "Requirement 1.2.3",
    "control_name": "Network Segmentation",
    "change_description": "Updated to include cloud environments"
  },
  "use_ai": false,  // Optional, default false
  "top_n": 5        // Optional, default 5
}
```

**Response:**
```json
{
  "success": true,
  "control": { /* original control */ },
  "matches": [
    {
      "type": "subpolicy",
      "policy_id": 123,
      "policy_name": "Network Security",
      "subpolicy_id": 456,
      "subpolicy_name": "Network Segmentation",
      "identifier": "1.2.3",
      "score": 0.89,
      "hybrid_score": 0.85,
      "ai_score": 0.93,
      "path": "Policy: Network Security > Sub-Policy: Network Segmentation"
    }
  ],
  "total_matches": 5,
  "use_ai": false
}
```

#### POST `/framework-comparison/{framework_id}/batch-match/`

Match multiple controls at once.

**Request:**
```json
{
  "controls": [
    {
      "control_id": "Requirement 1.2.3",
      "control_name": "Network Segmentation",
      "change_description": "..."
    },
    // ... more controls
  ],
  "use_ai": false  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "total_controls": 10,
  "matches": {
    "Requirement 1.2.3": [ /* array of matches */ ],
    "Requirement 2.1.1": [ /* array of matches */ ]
  },
  "use_ai": false
}
```

### 3. Frontend Service: `frameworkComparisonService.js`

**Methods:**

- `findControlMatches(frameworkId, control, useAI, topN)`
  - Calls API to find matches for a single control
  - Returns match results with scores

- `batchMatchControls(frameworkId, controls, useAI)`
  - Batch matches multiple controls
  - More efficient for large datasets

### 4. Vue Component: `FrameworkComparisonUpdated.vue`

**New Features:**

1. **AI Toggle Button**
   - Switch between text-based and AI-powered matching
   - Located in filters bar

2. **Find Matches Button**
   - Appears on each modified control
   - Click to find matching origin items
   - Shows loading spinner during processing

3. **Matches Panel**
   - Displays top 5 matches for selected control
   - Shows match type (policy/subpolicy/compliance)
   - Visual score bar with percentage
   - Ranked by similarity score

4. **Highlighting**
   - Matched items in origin are highlighted with blue border
   - Match score badge displayed on matched items
   - Selected control highlighted with green border

5. **Auto-expand**
   - Best matching policy/subpolicy automatically expands
   - User can immediately see the matched content

## Similarity Scoring Algorithm

### Hybrid Mode (Default)

Combines multiple factors with weighted scoring:

1. **ID Similarity (Weight: 3.0)**
   - Extracts numeric patterns from IDs
   - Matches "Requirement 1.2.3" with "1.2.3" or "Req. 1.2.3"
   - High weight because IDs are strong indicators

2. **Name/Title Similarity (Weight: 2.0)**
   - Compares control names using sequence matching
   - "Network Segmentation" vs "Network Segmentation Requirements"
   - Medium-high weight

3. **Description Similarity (Weight: 1.5)**
   - Compares change descriptions with policy descriptions
   - Considers full text content
   - Medium weight

4. **Keyword Overlap (Weight: 1.0)**
   - Extracts significant keywords (4+ characters)
   - Filters common stop words
   - Calculates Jaccard similarity
   - Lower weight

**Final Score:** Weighted average of all factors (0.0 - 1.0)

### AI Mode (Optional)

When enabled:
1. Generates OpenAI embeddings for control and origin items
2. Calculates cosine similarity between embeddings
3. Combines with hybrid score: `0.6 * hybrid + 0.4 * ai`
4. More accurate for semantic similarities
5. Requires OpenAI API key
6. Slower (adds 1-2 seconds per match)

## Usage

### Basic Usage

1. Select a framework with amendments
2. Click the magnifying glass icon on any modified control
3. View top 5 matches in the matches panel
4. Highlighted items show in the origin side
5. Click "Clear Matches" to reset

### With AI Matching

1. Toggle "AI Matching" button to ON
2. Click find matches on a control
3. Get more accurate semantic matches
4. AI matches consider meaning, not just text overlap

### Interpreting Scores

- **90-100%**: Very strong match, likely the same control
- **75-89%**: Strong match, high confidence
- **60-74%**: Good match, worth reviewing
- **40-59%**: Moderate match, some relation
- **<40%**: Weak match, may not be related

## Configuration

### Enable AI Matching

Set in Django settings:

```python
OPENAI_API_KEY = "sk-..."
OPENAI_MODEL = "gpt-4o-mini"  # or "gpt-4"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"  # or "text-embedding-3-large"
```

### Performance Tuning

**Hybrid Mode (Fast):**
- Average time: 0.5-1 second per control
- No external API calls
- Good for most use cases

**AI Mode (Accurate):**
- Average time: 2-4 seconds per control
- Requires OpenAI API
- Cost: ~$0.0001 per control match
- Better for complex semantic matching

## Examples

### Example 1: PCI DSS Requirement Match

**Target Control:**
```
ID: Requirement 1.2.3
Name: Network Segmentation
Description: Updated to include cloud environments and virtualized networks
```

**Best Match (Score: 92%):**
```
Type: Sub-Policy
Path: Policy: Network Security > Sub-Policy: Network Segmentation
ID: 1.2.3
Name: Network Segmentation Requirements
```

### Example 2: NIST Control Match

**Target Control:**
```
ID: AC-2(7)
Name: Account Management | Privileged User Accounts
Description: Enhanced monitoring requirements for privileged accounts
```

**Best Match (Score: 88%):**
```
Type: Compliance
Path: Policy: Access Control > Sub-Policy: Account Management > Compliance: Privileged Account Monitoring
ID: AC-2-07
```

## Troubleshooting

### Issue: Low Match Scores

**Possible Causes:**
- Control IDs use different naming conventions
- Descriptions are very different
- Framework structure has changed significantly

**Solutions:**
- Enable AI Matching for semantic similarity
- Manually review top matches
- Check if framework was restructured

### Issue: AI Matching Not Working

**Check:**
1. `OPENAI_API_KEY` is set in settings
2. OpenAI package is installed: `pip install openai`
3. API key is valid and has credits
4. Check Django logs for error messages

### Issue: Slow Performance

**For Single Matches:**
- Use hybrid mode (default) instead of AI
- Should be 0.5-1 second per control

**For Batch Matching:**
- Use batch endpoint instead of individual calls
- Process in background for large datasets

## Future Enhancements

1. **Caching**
   - Cache embeddings to avoid regenerating
   - Store match results for frequently accessed controls

2. **Machine Learning**
   - Train custom model on framework mappings
   - Learn from user feedback on match quality

3. **Advanced Filters**
   - Filter by match type (policy/subpolicy/compliance)
   - Filter by minimum score threshold

4. **Visualization**
   - Show relationship graph between origin and target
   - Visual mapping of framework changes

5. **Export**
   - Export match mappings to CSV/Excel
   - Generate mapping documentation

## API Cost Estimate

**Using text-embedding-3-small:**
- Per control match: ~$0.0001
- 100 controls: ~$0.01
- 1000 controls: ~$0.10

**Using text-embedding-3-large:**
- Per control match: ~$0.0003
- 100 controls: ~$0.03
- 1000 controls: ~$0.30

## Testing

```bash
# Test with hybrid matching
python manage.py shell
>>> from grc.routes.changemanagement.similarity_matcher import get_similarity_matcher
>>> matcher = get_similarity_matcher()
>>> control = {
...     'control_id': 'Requirement 1.2.3',
...     'control_name': 'Network Segmentation',
...     'change_description': 'Updated for cloud environments'
... }
>>> # Need origin_data with policies structure
>>> matches = matcher.find_best_matches(control, origin_data, top_n=3, use_ai=False)
>>> print(matches)
```

## License

MIT

## Contact

For questions or issues, contact the development team.


