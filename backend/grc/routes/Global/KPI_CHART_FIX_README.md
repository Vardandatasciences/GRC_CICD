# KPI Chart Visualization Fix

## Problem
KPIs were displaying raw JSON arrays instead of proper charts on the frontend.

## Solution
This fix automatically detects data types and assigns appropriate chart visualizations.

---

## 🚀 Quick Start - Fix All KPIs

### Method 1: Django Management Command (Recommended)

```bash
# Navigate to backend directory
cd backend

# Preview what will be changed (safe - no database changes)
python manage.py fix_kpi_charts --preview

# Apply the fixes (will ask for confirmation)
python manage.py fix_kpi_charts

# Fix a specific KPI
python manage.py fix_kpi_charts --kpi-id 5 --type "Line Chart"

# Show available chart types
python manage.py fix_kpi_charts --show-types
```

### Method 2: Django Shell

```bash
cd backend
python manage.py shell
```

Then in the shell:

```python
from grc.routes.Global.update_kpi_display_types import *

# Preview changes first
preview_kpi_changes()

# Apply changes
analyze_and_update_kpis()

# Fix specific KPI manually
fix_specific_kpi(kpi_id=5, display_type='Line Chart')

# Show available types
show_available_chart_types()
```

---

## 📊 Available Chart Types

The system supports these chart types:

| Chart Type | Best For | Data Size |
|------------|----------|-----------|
| **Line Chart** | Trends, time series | 20+ points |
| **Bar Chart** | Categorical comparison | 5-20 items |
| **Pie Chart** | Parts of whole | 3-5 categories |
| **Doughnut** | Distribution | 3-5 categories |
| **Gauge** | Single percentage (0-100) | 1 value |
| **Number** | Single numeric value | 1 value |
| **Percentage** | Single percentage with progress | 1 value |
| **Progress Bar** | Horizontal progress bar | 1 value |
| **Decimal** | Decimal number | 1 value |
| **Radar** | Multi-dimensional comparison | 3-8 dimensions |
| **Polar Area** | Area emphasis comparison | 3-8 categories |
| **Table** | Structured row/column data | Objects/Arrays |

---

## 🤖 Auto-Detection Logic

The script uses intelligent rules to suggest chart types:

### For Arrays:
- **30+ values** → Line Chart (time series/trends)
- **11-30 values** → Bar Chart or Line Chart (depending on positive/negative)
- **6-10 values** → Bar Chart or Doughnut (based on value range)
- **2-5 values** → Doughnut or Bar Chart (for distribution)
- **1 value** → Gauge or Number (based on range)

### For Single Values:
- **0-100 range** → Gauge or Percentage
- **Other numbers** → Number display
- **Objects** → Table

---

## 🔍 Preview Before Applying

Always preview first to see what will change:

```bash
python manage.py fix_kpi_charts --preview
```

Example output:
```
📊 KPIS REQUIRING CHANGES: 15

KPI #1: Risk Exposure Trend
  Module: Risk
  Current Type: None
  Suggested Type: ✨ Line Chart
  Reason: Long series (45 points) - best for trends
  Value Preview: [6607.58, 7372.88999999999, 8531.9, ...]

KPI #5: Risk Distribution
  Module: Risk
  Current Type: Number
  Suggested Type: ✨ Doughnut
  Reason: Very short series (4 items) - distribution
  Value Preview: [4.0, 4.0, 3.0, 3.0]
```

---

## 🎯 Manual Override for Specific KPIs

If you want to set a specific chart type:

```bash
# Using management command
python manage.py fix_kpi_charts --kpi-id 10 --type "Radar"

# Using shell
fix_specific_kpi(kpi_id=10, display_type='Radar')
```

---

## 🔄 Frontend Changes

The frontend now includes:

### Smart Detection
- Automatically detects array data
- Prevents raw JSON display
- Falls back to appropriate charts

### New Display Rules
- Arrays **always** show as charts (never as raw text)
- Single values show as styled numbers or gauges
- Unknown types default to line charts for arrays

### Error Handling
- If data can't be visualized, shows a clean error icon
- No more raw JSON visible to users

---

## 📝 Database Schema

The `Kpi` table has these relevant fields:

```python
KpiId (int) - Primary key
Name (varchar) - KPI name
Value (text) - The data (can be JSON array, number, etc.)
DisplayType (varchar) - Chart type: 'Line Chart', 'Bar Chart', etc.
DataType (varchar) - Data categorization
Module (varchar) - Which module owns this KPI
```

---

## 🐛 Troubleshooting

### KPIs still showing as text?
1. Run the fix script
2. Clear browser cache
3. Hard refresh (Ctrl+Shift+R)

### Want different chart types?
Edit the KPI manually:
```sql
UPDATE Kpi 
SET DisplayType = 'Radar' 
WHERE KpiId = 10;
```

Or use the command:
```bash
python manage.py fix_kpi_charts --kpi-id 10 --type "Radar"
```

### Check current KPI types:
```sql
SELECT KpiId, Name, DisplayType, LEFT(Value, 50) as ValuePreview
FROM Kpi
ORDER BY KpiId;
```

---

## ✅ Testing

After applying fixes:

1. **Refresh frontend** (hard refresh)
2. **Check KPI Dashboard** - Should see charts, not raw data
3. **Filter by module** - Verify all modules display properly
4. **Check console** - No errors related to chart rendering

---

## 📚 Code Files Changed

### Frontend:
- `frontend/src/components/AiKpis/kpi.vue` - Smart detection logic
- `frontend/src/components/AiKpis/kpi.css` - Error display styling

### Backend:
- `backend/grc/routes/Global/update_kpi_display_types.py` - Detection algorithm
- `backend/grc/management/commands/fix_kpi_charts.py` - Management command

---

## 🎉 Expected Result

**Before:**
```
[6607.58, 7372.88999999999, 8531.9, 9227.13000000001, ...]
```

**After:**
```
📈 Beautiful line chart showing trend over time
```

---

## 💡 Tips

1. **Always preview first** - See changes before applying
2. **Backup database** - Before running updates (optional)
3. **Module-specific charts** - Different modules may need different chart types
4. **Custom override** - Use manual fix for specific requirements
5. **Regular maintenance** - Run when adding new KPIs

---

## 🆘 Need Help?

If you encounter issues:

1. Check Django logs: `backend/logs/`
2. Check browser console for frontend errors
3. Verify database connection
4. Ensure Chart.js is loaded properly

---

## 📅 Maintenance

Run this script whenever:
- New KPIs are added
- KPI values change significantly
- Display types seem incorrect
- After database migrations

---

**Happy Charting! 📊✨**

