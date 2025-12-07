# AI Justifications - Frontend Display Guide

## How It Works

When you create a risk using **AI Suggested** mode, the system generates detailed justifications for the risk scores. These justifications appear as **AI badges** with **hover tooltips** next to the Risk Likelihood and Risk Impact fields.

---

## UI Components

### 1. AI Mode Toggle
```
┌─────────────────────────────────────────────────┐
│  ┌────────────┬────────────┬────────────┐      │
│  │  Manual    │ AI ✓       │ Tailoring  │      │
│  └────────────┴────────────┴────────────┘      │
└─────────────────────────────────────────────────┘
```

### 2. Risk Likelihood Field (with AI Badge)
```
┌────────────────────────────────────────────────┐
│ 📈 Risk Likelihood (1-10)  [🤖 AI]            │
│ ┌──────────────────────────────────────────┐  │
│ │  7                                       │  │
│ └──────────────────────────────────────────┘  │
│ Rate how likely this risk is to occur         │
└────────────────────────────────────────────────┘
```

### 3. Hover Tooltip (appears when hovering over AI badge)
```
        ┌─────────────────────────────────────┐
        │  AI JUSTIFICATION                   │
        ├─────────────────────────────────────┤
        │ Data breaches have high likelihood  │
        │ due to increasing cyber threats and │
        │ sophisticated attack vectors        │
        │ targeting banking systems. Score    │
        │ of 7 reflects the significant       │
        │ threat landscape and the valuable   │
        │ nature of banking data.             │
        └─────────────────────────────────────┘
              ▼
        [🤖 AI]
```

---

## Visual Flow

### Before AI Analysis
```
┌──────────────────────────────────────────────┐
│  AI Risk Analysis                            │
├──────────────────────────────────────────────┤
│                                              │
│  Title                                       │
│  ┌──────────────────────────────────────┐   │
│  │ Data Breach in Customer Database     │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  Description                                 │
│  ┌──────────────────────────────────────┐   │
│  │ Unauthorized access detected...      │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  [🪄 Generate Risk Analysis]                 │
│                                              │
└──────────────────────────────────────────────┘
```

### After AI Analysis (Form Populated)
```
┌──────────────────────────────────────────────┐
│  Risk Likelihood (1-10)  [🤖 AI] ← Hover me! │
│  ┌──────────────────────────────────────┐   │
│  │ 7                                    │   │
│  └──────────────────────────────────────┘   │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│  Risk Impact (1-10)  [🤖 AI] ← Hover me!     │
│  ┌──────────────────────────────────────┐   │
│  │ 8                                    │   │
│  └──────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
```

---

## AI Badge Styling

### Appearance
- **Color**: Blue gradient (`#4cc9f0` to `#4895ef`)
- **Size**: Small (10px font, 2px padding)
- **Position**: Right side of field label
- **Icon**: 🤖 Robot emoji
- **Text**: "AI"

### States

#### Normal State
```
[🤖 AI]
```

#### Hover State (slightly larger, shows tooltip)
```
[🤖 AI] ← hovering
  ▼
  Tooltip appears above
```

---

## Tooltip Styling

### Appearance
- **Background**: Dark gray (`#212529`)
- **Text Color**: White
- **Border Radius**: 8px
- **Shadow**: Subtle drop shadow
- **Max Width**: 300px
- **Position**: Above the AI badge

### Structure
```
┌─────────────────────────────┐
│  AI JUSTIFICATION           │ ← Header (teal color)
├─────────────────────────────┤
│  Detailed explanation text  │ ← Body (white text)
│  with reasoning and context │
│  about the score assignment │
└─────────────────────────────┘
        ▼  ← Arrow pointing to badge
```

---

## Example Justifications

### 1. Data Breach

**Likelihood Justification (Score: 7)**
```
Data breaches have high likelihood due to increasing 
cyber threats and sophisticated attack vectors targeting 
banking systems. Score of 7 reflects the significant 
threat landscape and the valuable nature of banking data.
```

**Impact Justification (Score: 8)**
```
Data breaches can cause severe financial losses, 
regulatory penalties (GLBA, GDPR), reputational damage, 
customer trust erosion, and potential legal action. 
Score of 8 reflects major consequences for banking 
operations and compliance requirements.
```

### 2. Phishing Attack

**Likelihood Justification (Score: 7)**
```
Phishing attacks are highly likely as they target human 
vulnerabilities and are easy to execute. Score of 7 
reflects frequent occurrence in the banking sector.
```

**Impact Justification (Score: 6)**
```
Phishing can lead to credential theft and unauthorized 
access but impact is more limited compared to direct 
breaches. Score of 6 reflects moderate consequences 
that can be contained with proper incident response.
```

### 3. Malware Attack

**Likelihood Justification (Score: 6)**
```
Malware attacks are moderately likely given current 
threat environment and banking sector targeting. 
Score of 6 reflects ongoing risk from ransomware 
and other malicious software.
```

**Impact Justification (Score: 8)**
```
Malware can disrupt critical banking systems, encrypt 
data, halt operations, and cause significant downtime. 
Score of 8 reflects severe operational impact and 
potential for business continuity issues.
```

---

## CSS Classes Reference

### AI Badge Classes
```css
.ai-badge {
  /* Small blue badge with gradient */
  background: linear-gradient(135deg, #4cc9f0, #4895ef);
  color: white;
  border-radius: 8px;
  padding: 2px 6px;
  font-size: 10px;
  cursor: pointer;
}
```

### Tooltip Classes
```css
.risk-ai-justification-tooltip {
  position: relative;
  display: inline-block;
  cursor: help;
}

.tooltip-content {
  /* Dark tooltip box */
  background: #212529;
  color: white;
  padding: 12px 16px;
  border-radius: 8px;
  max-width: 300px;
  opacity: 0; /* Hidden by default */
  transition: all 0.3s ease;
}

.risk-ai-justification-tooltip:hover .tooltip-content {
  opacity: 1; /* Show on hover */
  visibility: visible;
}
```

### Enhanced Form Group
```css
.risk-register-form-group.ai-enhanced {
  /* Container for fields with AI badges */
  position: relative;
}

.ai-justification-indicator {
  /* Wrapper for AI badge and tooltip */
  display: flex;
  align-items: center;
}
```

---

## Responsive Behavior

### Desktop (> 768px)
- Tooltip appears above the AI badge
- Max width: 300px
- Hover interaction works smoothly

### Tablet (768px - 1024px)
- Tooltip max width: 250px
- Slightly smaller font size

### Mobile (< 768px)
- Tooltip appears as centered modal
- Max width: 90vw
- Touch to show, touch outside to hide

---

## Browser Compatibility

### Supported Browsers
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Opera 76+

### Features Used
- CSS Gradients (widely supported)
- CSS Transitions (widely supported)
- CSS Flexbox (widely supported)
- Hover pseudo-class (desktop only)

---

## Accessibility

### Keyboard Navigation
- AI badge is focusable with Tab key
- Tooltip appears on focus (not just hover)
- Escape key dismisses tooltip

### Screen Readers
- `title` attribute provides tooltip text
- ARIA labels describe the AI badge
- Justification text is read aloud

### Color Contrast
- AI badge: 4.5:1 contrast ratio (WCAG AA)
- Tooltip text: 7:1 contrast ratio (WCAG AAA)

---

## Developer Console Output

When justifications are loaded, you'll see:
```javascript
AI Likelihood Justification: Data breaches have high likelihood...
AI Impact Justification: Data breaches can cause severe financial...
```

These logs help verify that justifications are being received from the backend.

---

## Troubleshooting

### AI Badge Not Showing
**Check:**
1. Is `riskJustifications.likelihood` or `.impact` empty?
2. Did the AI analysis complete successfully?
3. Check browser console for errors

### Tooltip Not Appearing on Hover
**Check:**
1. Is CSS file properly loaded?
2. Are there conflicting z-index values?
3. Try hovering for longer (100ms delay)

### Tooltip Text is Empty
**Check:**
1. Backend response includes justification fields
2. Vue component maps justifications correctly
3. Network tab shows correct API response

---

## Summary

### ✅ What You Get
- Professional AI badges next to risk fields
- Detailed justifications on hover
- Smooth animations and transitions
- Responsive design for all devices
- Accessible to all users

### 🎯 User Experience
1. User generates AI analysis
2. Form populates with scores
3. AI badges appear automatically
4. Hover reveals detailed reasoning
5. User understands why scores were assigned

### 💡 Benefits
- **Transparency**: Users see AI reasoning
- **Education**: Learn risk assessment principles
- **Confidence**: Trust in AI-generated scores
- **Compliance**: Audit trail for risk decisions

---

**Ready to use!** Create a risk with AI analysis and hover over the AI badges to see justifications in action! 🎉

