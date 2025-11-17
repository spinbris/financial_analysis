# Gradio Theme Pollution Fix

## Problem
The Gradio web interface displayed dark text on dark backgrounds, making the UI unreadable.

**Symptoms:**
- Dark backgrounds on sections
- Dark text that's invisible against dark backgrounds
- Headers like "View Existing Analysis" and "Run New Analysis" barely visible
- Overall UI corruption

## Root Cause
Gradio 4.x automatically detects the browser/system's dark mode preference and applies dark mode styling, which overrides the custom light theme configured in the code.

## Solution Applied

**File:** `financial_research_agent/web_app.py`
**Lines:** 992-1000

Added JavaScript to force light theme on page load:

```python
with gr.Blocks(
    theme=create_theme(),
    title="Financial Research Agent",
    js="""
    function refresh() {
        const url = new URL(window.location);
        if (url.searchParams.get('__theme') !== 'light') {
            url.searchParams.set('__theme', 'light');
            window.location.href = url.href;
        }
    }
    """,
    css="""
    ...
```

## How It Works

1. JavaScript runs on page load
2. Checks URL for `__theme` parameter
3. If not set to 'light', adds `?__theme=light` to URL
4. Reloads page once with correct theme
5. Disables Gradio's automatic dark mode detection

## Testing

After restarting the web app:
1. Navigate to `http://localhost:7860/`
2. Page will automatically redirect to `http://localhost:7860/?__theme=light`
3. Light theme should be visible with:
   - Light backgrounds on all sections
   - Dark text clearly visible
   - Headers and labels readable
   - Proper contrast throughout

## Alternative Manual Fix

If automatic fix doesn't work, manually add theme parameter to URL:
- Current: `http://localhost:7860/`
- Fixed: `http://localhost:7860/?__theme=light`

## Why This Happened

This is a known behavior in Gradio 4.x:
- Gradio respects browser/system dark mode settings
- Custom themes can be overridden by browser preferences
- No native Python parameter exists to disable this
- JavaScript workaround is the recommended solution

## Related Issue

This is unrelated to the banking ratios implementation - it's a Gradio framework behavior that was always present but may have been triggered by browser settings or a Gradio version update.

---

**Fixed:** November 13, 2025
**Lines Changed:** 8 lines (added `js` parameter)
**Breaking Changes:** None
**Impact:** UI now displays correctly regardless of browser dark mode setting
