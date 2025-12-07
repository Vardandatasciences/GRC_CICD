# Policy Status Calculation Explanation

## Overview
This document explains how the system calculates **Applied**, **In Progress**, and **Pending** policy counts and percentages for the donut chart on the homepage.

## Calculation Logic

### Step 1: Filter Policies by Framework
```python
# Get all policies for the selected framework
policies_qs = Policy.objects.filter(framework_filter) if framework_filter else Policy.objects.all()
```
- If a framework is selected (e.g., Basel III Framework ID=336), only policies for that framework are included
- If no framework is selected, all policies are included

### Step 2: Filter to Only Active Policies
```python
# Only count policies that are Active (not Inactive/Deleted)
active_policies_qs = policies_qs.filter(ActiveInactive='Active')
```
- **Important**: Only policies with `ActiveInactive='Active'` are counted
- Inactive or deleted policies are excluded from all calculations

### Step 3: Count Total Active Policies
```python
total_policies = active_policies_qs.count()
```
- This is the denominator for percentage calculations
- Example: If Basel III has 7 active policies, `total_policies = 7`

### Step 4: Categorize Policies by Status

#### A. APPLIED (Green Segment)
```python
applied = active_policies_qs.filter(Status='Approved').count()
```
- **Criteria**: `Status = 'Approved'` AND `ActiveInactive = 'Active'`
- These are policies that have been approved and are currently active   
- Example: 4 policies with status "Approved" → `applied = 4`

#### B. IN PROGRESS (Orange Segment)
```python
in_progress = active_policies_qs.filter(Status='Under Review').count()
```
- **Criteria**: `Status = 'Under Review'` AND `ActiveInactive = 'Active'`
- These are policies currently being reviewed/assessed
- Example: 2 policies with status "Under Review" → `in_progress = 2`

#### C. PENDING (Red Segment)
```python
pending = active_policies_qs.filter(Status__in=['Draft', 'Pending']).count()
```
- **Criteria**: `Status IN ('Draft', 'Pending')` AND `ActiveInactive = 'Active'`
- These are policies that are drafted but not yet submitted for review
- Example: 0 policies with status "Draft" or "Pending" → `pending = 0`

### Step 5: Calculate Percentages
```python
applied_pct = round((applied / total_policies * 100), 1) if total_policies > 0 else 0
in_progress_pct = round((in_progress / total_policies * 100), 1) if total_policies > 0 else 0
pending_pct = round((pending / total_policies * 100), 1) if total_policies > 0 else 0
```

**Formula**: `(Category Count / Total Active Policies) × 100`

#### Example Calculation (Basel III Framework):
- **Total Active Policies**: 7
- **Applied**: 4 policies
  - Percentage: `(4 / 7) × 100 = 57.1%`
- **In Progress**: 2 policies
  - Percentage: `(2 / 7) × 100 = 28.6%`
- **Pending**: 0 policies
  - Percentage: `(0 / 7) × 100 = 0.0%`

**Note**: Percentages may not add up to exactly 100% if there are policies with other statuses (e.g., "Rejected", "Cancelled") that are not included in these three categories.

## Data Flow

```
Database Query
    ↓
Filter by Framework (if selected)
    ↓
Filter by ActiveInactive='Active'
    ↓
    ├─→ Count Total: 7
    ├─→ Count Applied (Status='Approved'): 4
    ├─→ Count In Progress (Status='Under Review'): 2
    └─→ Count Pending (Status IN ['Draft', 'Pending']): 0
    ↓
Calculate Percentages
    ↓
Fetch Policy Details for Popup
    ↓
Return JSON Response
```

## Status Mapping

| Status Value | Category | Display Color |
|-------------|----------|---------------|
| `'Approved'` | **Applied** | Green (#10b981) |
| `'Under Review'` | **In Progress** | Orange (#f59e0b) |
| `'Draft'` | **Pending** | Red (#ef4444) |
| `'Pending'` | **Pending** | Red (#ef4444) |
| Other statuses | Not included | - |

## Important Notes

1. **Only Active Policies**: Policies with `ActiveInactive='Inactive'` are completely excluded
2. **Framework Filter**: When a framework is selected, only policies for that framework are counted
3. **Status Matching**: The system uses exact string matching for status values
4. **All Policies Returned**: The popup shows ALL policies (not limited) for the clicked segment
5. **Percentages are Rounded**: Percentages are rounded to 1 decimal place (e.g., 57.1%)

## Example from Backend Logs

```
Framework: Basel III Framework (ID: 336)
📊 Total ACTIVE policies queried: 7
📊 Applied (Approved + Active): 4
📊 In Progress (Under Review + Active): 2
📊 Pending (Draft/Pending + Active): 0
📊 Percentages - Applied: 57.1%, In Progress: 28.6%, Pending: 0.0%
```

This means:
- Out of 7 total active policies in Basel III framework
- 4 are Approved (57.1%)
- 2 are Under Review (28.6%)
- 0 are Draft/Pending (0%)
- 1 policy might have a different status (not shown in donut chart)

