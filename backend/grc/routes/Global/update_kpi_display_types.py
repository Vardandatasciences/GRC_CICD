"""
KPI Display Type Auto-Detection and Update Script
This script analyzes KPI values and suggests/updates appropriate display types
Run this to ensure all KPIs have proper chart types assigned

Usage:
    python manage.py shell
    >>> from grc.routes.Global.update_kpi_display_types import analyze_and_update_kpis, preview_kpi_changes
    >>> preview_kpi_changes()  # Preview changes before applying
    >>> analyze_and_update_kpis()  # Apply changes
"""

import json
from grc.models import Kpi


def detect_display_type(value, current_display_type=None):
    """
    Analyze KPI value and determine the best display type
    Returns: (display_type, reason)
    """
    if not value:
        return ('Number', 'No value provided')
    
    try:
        # Try to parse as JSON
        parsed = json.loads(value) if isinstance(value, str) else value
        
        # Check if it's an array
        if isinstance(parsed, list):
            data_length = len(parsed)
            
            # Check if all values are numeric
            all_numeric = all(isinstance(x, (int, float)) for x in parsed)
            if not all_numeric:
                return ('Table', 'Array contains non-numeric values')
            
            # Very long series - time series/trend data
            if data_length > 30:
                return ('Line Chart', f'Long series ({data_length} points) - best for trends')
            
            # Medium length series
            elif data_length > 10 and data_length <= 30:
                # Check if all positive (could be bar or line)
                all_positive = all(x >= 0 for x in parsed)
                if all_positive:
                    return ('Bar Chart', f'Medium series ({data_length} points) - good for comparison')
                else:
                    return ('Line Chart', f'Medium series ({data_length} points) with negative values')
            
            # Short series
            elif data_length > 5 and data_length <= 10:
                all_positive = all(x >= 0 for x in parsed)
                if all_positive:
                    max_val = max(parsed)
                    if max_val <= 100:
                        return ('Doughnut', f'Short series ({data_length} points) - part of whole visualization')
                    else:
                        return ('Bar Chart', f'Short series ({data_length} points) - categorical comparison')
                else:
                    return ('Line Chart', f'Short series ({data_length} points) with mixed values')
            
            # Very short series (2-5 items)
            elif data_length >= 2 and data_length <= 5:
                all_positive = all(x >= 0 for x in parsed)
                if all_positive and max(parsed) <= 100:
                    return ('Doughnut', f'Very short series ({data_length} items) - distribution')
                elif all_positive:
                    return ('Bar Chart', f'Very short series ({data_length} items) - comparison')
                else:
                    return ('Bar Chart', f'Very short series ({data_length} items) with negative values')
            
            # Single value in array
            elif data_length == 1:
                single_val = parsed[0]
                if 0 <= single_val <= 100:
                    return ('Gauge', 'Single percentage-like value')
                else:
                    return ('Number', 'Single numeric value')
        
        # Check if it's a dictionary/object (for tables)
        elif isinstance(parsed, dict):
            return ('Table', 'Object data - best displayed as table')
        
        # Single numeric value
        elif isinstance(parsed, (int, float)):
            if 0 <= parsed <= 100:
                return ('Gauge', 'Single value in percentage range')
            elif parsed >= 0:
                return ('Number', 'Single positive numeric value')
            else:
                return ('Number', 'Single numeric value with sign')
        
        # String value
        else:
            return ('Number', 'Non-numeric value')
            
    except (json.JSONDecodeError, ValueError, TypeError):
        # Not JSON, treat as single value
        try:
            num_val = float(value)
            if 0 <= num_val <= 100:
                return ('Percentage', 'Single percentage value')
            else:
                return ('Number', 'Single numeric value')
        except (ValueError, TypeError):
            return ('Number', 'Non-parseable value')
    
    return ('Number', 'Default fallback')


def preview_kpi_changes():
    """
    Preview what changes would be made without actually updating the database
    """
    print("=" * 80)
    print("KPI DISPLAY TYPE ANALYSIS - PREVIEW MODE")
    print("=" * 80)
    print()
    
    kpis = Kpi.objects.all()
    changes = []
    no_changes = []
    
    for kpi in kpis:
        current_type = kpi.DisplayType or 'None'
        suggested_type, reason = detect_display_type(kpi.Value, current_type)
        
        if current_type != suggested_type:
            changes.append({
                'id': kpi.KpiId,
                'name': kpi.Name,
                'module': kpi.Module,
                'current': current_type,
                'suggested': suggested_type,
                'reason': reason,
                'value_preview': str(kpi.Value)[:100] + '...' if len(str(kpi.Value)) > 100 else str(kpi.Value)
            })
        else:
            no_changes.append({
                'id': kpi.KpiId,
                'name': kpi.Name,
                'current': current_type
            })
    
    print(f"\n📊 KPIS REQUIRING CHANGES: {len(changes)}")
    print("-" * 80)
    for change in changes:
        print(f"\nKPI #{change['id']}: {change['name']}")
        print(f"  Module: {change['module']}")
        print(f"  Current Type: {change['current']}")
        print(f"  Suggested Type: ✨ {change['suggested']}")
        print(f"  Reason: {change['reason']}")
        print(f"  Value Preview: {change['value_preview']}")
    
    print(f"\n\n✅ KPIS ALREADY CORRECT: {len(no_changes)}")
    print("-" * 80)
    for kpi in no_changes[:5]:  # Show first 5
        print(f"  KPI #{kpi['id']}: {kpi['name']} ({kpi['current']})")
    if len(no_changes) > 5:
        print(f"  ... and {len(no_changes) - 5} more")
    
    print("\n" + "=" * 80)
    print(f"SUMMARY: {len(changes)} changes needed, {len(no_changes)} already correct")
    print("=" * 80)
    print("\nTo apply these changes, run: analyze_and_update_kpis()")
    print()
    
    return changes


def analyze_and_update_kpis(dry_run=False):
    """
    Analyze all KPIs and update their display types based on value content
    
    Args:
        dry_run (bool): If True, only show what would be changed without updating
    """
    if dry_run:
        return preview_kpi_changes()
    
    print("=" * 80)
    print("UPDATING KPI DISPLAY TYPES")
    print("=" * 80)
    print()
    
    kpis = Kpi.objects.all()
    updated_count = 0
    skipped_count = 0
    
    for kpi in kpis:
        current_type = kpi.DisplayType
        suggested_type, reason = detect_display_type(kpi.Value, current_type)
        
        if current_type != suggested_type:
            print(f"Updating KPI #{kpi.KpiId}: {kpi.Name}")
            print(f"  {current_type or 'None'} → {suggested_type}")
            print(f"  Reason: {reason}")
            
            kpi.DisplayType = suggested_type
            kpi.save()
            updated_count += 1
        else:
            skipped_count += 1
    
    print("\n" + "=" * 80)
    print(f"✅ Updated: {updated_count} KPIs")
    print(f"⏭️  Skipped: {skipped_count} KPIs (already correct)")
    print("=" * 80)
    print("\n🎉 All KPIs have been updated! Refresh your frontend to see charts.\n")
    
    return updated_count


def fix_specific_kpi(kpi_id, display_type):
    """
    Manually set a specific KPI's display type
    
    Args:
        kpi_id (int): The KPI ID to update
        display_type (str): One of: 'Line Chart', 'Bar Chart', 'Pie Chart', 
                           'Doughnut', 'Gauge', 'Radar', 'Polar', 'Number', 
                           'Percentage', 'Table', 'Decimal', 'Progress Bar'
    """
    try:
        kpi = Kpi.objects.get(KpiId=kpi_id)
        old_type = kpi.DisplayType
        kpi.DisplayType = display_type
        kpi.save()
        
        print(f"✅ Updated KPI #{kpi_id}: {kpi.Name}")
        print(f"   {old_type or 'None'} → {display_type}")
        return True
    except Kpi.DoesNotExist:
        print(f"❌ KPI #{kpi_id} not found")
        return False


def show_available_chart_types():
    """
    Display all available chart types
    """
    print("\n📊 AVAILABLE CHART TYPES:\n")
    chart_types = [
        ("Line Chart", "Best for trends and time series data (20+ points)"),
        ("Bar Chart", "Best for categorical comparisons (5-20 items)"),
        ("Pie Chart", "Best for showing parts of a whole (3-5 categories)"),
        ("Doughnut", "Similar to Pie but with center hole (3-5 categories)"),
        ("Gauge", "Best for single percentage values (0-100)"),
        ("Radar", "Best for multi-dimensional comparisons (3-8 dimensions)"),
        ("Polar Area", "Similar to Radar with area emphasis"),
        ("Number", "Single numeric value display with styling"),
        ("Percentage", "Single percentage with circular progress"),
        ("Decimal", "Single decimal number display"),
        ("Progress Bar", "Horizontal bar for percentage progress"),
        ("Table", "Structured data in rows and columns"),
    ]
    
    for name, desc in chart_types:
        print(f"  • {name:20} - {desc}")
    print()


if __name__ == "__main__":
    print("\n⚠️  This script should be run from Django shell:")
    print("    python manage.py shell")
    print("    >>> from grc.routes.Global.update_kpi_display_types import *")
    print("    >>> preview_kpi_changes()  # Preview first")
    print("    >>> analyze_and_update_kpis()  # Then apply\n")
