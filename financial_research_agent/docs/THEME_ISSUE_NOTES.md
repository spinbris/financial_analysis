# Theme Switching Issue - Investigation Notes

## User Report

"app them switched from light to dark"

## Investigation

### Current Theme Configuration

The web app uses a custom Morningstar-inspired light theme defined in [web_app.py:16-39](financial_research_agent/web_app.py:16-39):

```python
def create_theme():
    """Create a professional Morningstar-style theme."""
    return gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="slate",
        neutral_hue="slate",
    ).set(
        body_background_fill="#f5f7fa",  # Light gray background
        body_text_color="#1a1d1f",        # Dark text
        block_background_fill="white",    # White cards
        # ... more light theme settings
    )
```

### Possible Causes

1. **Browser Dark Mode Preference**
   - Most modern browsers respect OS-level dark mode settings
   - Gradio may auto-switch based on `prefers-color-scheme: dark` media query
   - Chrome, Firefox, Safari all have auto dark mode features

2. **Gradio Default Behavior**
   - Gradio has built-in dark mode support
   - May override custom theme if browser requests dark mode
   - No explicit `js_dark_mode=False` setting found in code

3. **CSS Media Query Interference**
   - Browser extensions (Dark Reader, etc.)
   - System-level dark mode switching during long analysis
   - CSS `@media (prefers-color-scheme: dark)` rules

### Current Status

- **No explicit dark mode control** in web_app.py
- **Custom light theme defined** but may be overridden
- **No theme lock** to prevent auto-switching

## Potential Solutions

### Solution 1: Force Light Mode (Recommended)

Add explicit theme control when launching Gradio:

```python
# In create_interface():
app = gr.Blocks(
    theme=create_theme(),
    css=custom_css,
    title="Financial Research Agent",
    js="() => { document.body.classList.remove('dark'); }"  # Force light mode
)
```

### Solution 2: Add Theme Toggle

Add user-controlled theme toggle button:

```python
with gr.Row():
    theme_toggle = gr.Button("🌙 Dark Mode", size="sm")
    theme_toggle.click(
        fn=None,
        js="() => { document.body.classList.toggle('dark'); }"
    )
```

### Solution 3: Respect User Preference But Lock During Session

Lock theme at start of analysis to prevent mid-analysis switching:

```python
async def generate_analysis(self, query, progress):
    # Lock theme at start
    js_code = "document.body.setAttribute('data-theme-locked', 'true');"

    # ... analysis code ...

    return results
```

## Recommendation

**Implement Solution 1** - Force light mode to match professional financial industry standards (Morningstar, Bloomberg, etc. all use light themes for data analysis).

If dark mode is desired:
1. Create proper dark theme version with readable financial tables
2. Add theme toggle for user control
3. Save preference in browser localStorage

## Status

- **Not yet fixed** - Needs user confirmation on preferred approach
- **Low priority** - Cosmetic issue, doesn't affect functionality
- **Easy fix** - Can be implemented in 5 minutes

---

**Date:** 2025-11-03
**Impact:** Cosmetic only - doesn't affect analysis quality or performance
**User Action Required:** Confirm preferred theme behavior (force light, add toggle, or respect browser)
