"""
Simple demonstration of KPI chart type detection
Run this to see what chart types would be assigned to your KPIs
"""

import json

def detect_chart_type(value_str):
    """Detect best chart type for a KPI value"""
    try:
        # Try to parse the value
        value = json.loads(value_str) if isinstance(value_str, str) else value_str
        
        if isinstance(value, list):
            length = len(value)
            
            # Long series - trends
            if length > 30:
                return "Line Chart", f"{length} data points - perfect for showing trends over time"
            
            # Medium series
            elif length > 10:
                all_positive = all(x >= 0 for x in value if isinstance(x, (int, float)))
                if all_positive:
                    return "Bar Chart", f"{length} data points - great for comparing categories"
                return "Line Chart", f"{length} data points with mixed values"
            
            # Short series
            elif length > 5:
                all_positive = all(x >= 0 for x in value if isinstance(x, (int, float)))
                return ("Doughnut", f"{length} categories - shows distribution") if all_positive else ("Bar Chart", f"{length} items")
            
            # Very short
            elif length >= 2:
                return "Doughnut", f"{length} categories - shows parts of whole"
            
            # Single value in array
            elif length == 1:
                val = value[0]
                if 0 <= val <= 100:
                    return "Gauge", "Single percentage value (0-100)"
                return "Number", "Single numeric value"
        
        # Single number
        elif isinstance(value, (int, float)):
            if 0 <= value <= 100:
                return "Gauge", f"Value: {value} - shows as progress indicator"
            return "Number", f"Value: {value} - shows as large styled number"
        
        # Object/dict
        elif isinstance(value, dict):
            return "Table", "Structured data - displays as table"
        
        return "Number", "Default display"
        
    except:
        return "Number", "Could not parse value"


# Example KPIs from your screenshots
example_kpis = [
    {
        "name": "Customer Due Diligence: Risk Exposure Over Time",
        "value": "[6607.58, 7372.88999999999, 8531.9, 9227.13000000001, 10452.25, 11802.59, 13302.7, 15152.810000000001, 16802.92, 18302.7, 19803.14, 423182.62]"
    },
    {
        "name": "Enhanced Due Diligence (EDD): Customer Risk Assessment Distribution", 
        "value": "[4.0, 4.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]"
    },
    {
        "name": "Customer Due Diligence: Risk Score Progression",
        "value": "[-4.0, 7.0, 5.0, -10.0, -5.0, 13.0, -4.0, 8.0, -5.0, -8.0, 4.0, 3.0, -5.0, -4.0, 12.0, 5.0, -12.0, 3.0, -5.0, -4.0]"
    },
    {
        "name": "Compliance Rate",
        "value": "85.5"
    },
    {
        "name": "Risk Distribution",
        "value": "[25, 35, 15, 20, 5]"
    }
]

print("\n" + "="*80)
print("KPI CHART TYPE DETECTION - DEMO")
print("="*80 + "\n")

for kpi in example_kpis:
    chart_type, reason = detect_chart_type(kpi['value'])
    
    print(f"KPI: {kpi['name']}")
    print(f"Current Display: RAW JSON/TEXT")
    print(f"New Display Type: {chart_type}")
    print(f"Reason: {reason}")
    
    # Show data preview
    try:
        value = json.loads(kpi['value'])
        if isinstance(value, list):
            if len(value) > 5:
                preview = f"{value[:3]} ... {value[-2:]}"
            else:
                preview = str(value)
        else:
            preview = str(value)
    except:
        preview = kpi['value'][:50]
    
    print(f"Data Preview: {preview}")
    print("-" * 80 + "\n")

print("\n" + "="*80)
print("RESULT: NO MORE RAW JSON - EVERYTHING WILL BE A CHART!")
print("="*80 + "\n")

print("To apply these changes to your database:")
print("1. Fix the Unicode encoding issue in incident_ai_import.py")
print("2. Run: python manage.py fix_kpi_charts --preview")
print("3. Run: python manage.py fix_kpi_charts")
print()

