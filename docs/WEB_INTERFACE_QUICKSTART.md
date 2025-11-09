# Web Interface Quick Start

## 🚀 Launch in 30 Seconds

```bash
# 1. Make sure you're in the project directory
cd /Users/stephenparton/projects/financial_analysis

# 2. Launch the web interface
.venv/bin/python launch_web_app.py

# That's it! The interface will open at http://localhost:7860
```

## 📱 Using the Interface

### Generate Your First Analysis

1. **Click a template** (recommended for first time):
   - Click "Tesla Q3 2025 Performance"

2. **Click "Generate Analysis"**
   - Wait 30-60 seconds while it:
     - Extracts data from SEC EDGAR
     - Analyzes financial statements
     - Calculates metrics
     - Generates comprehensive report

3. **View Results**:
   - Switch to "Comprehensive Report" tab for full analysis
   - Check "Financial Statements" for raw data
   - Review "Financial Metrics" for YoY comparisons
   - Verify "Data Verification" for quality assurance

### Custom Queries

Try these queries:
- "Analyze Apple's Q3 2025 financial health"
- "What are Microsoft's profitability trends?"
- "Compare Tesla and Ford's financial performance"
- "Is NVIDIA a good investment based on recent financials?"

## 🎨 What You'll See

### Professional Interface
- Clean, Morningstar-style design
- Blue and white color scheme
- Easy-to-read tables
- Trend indicators (↑/↓)

### Comprehensive Data
- **40-50 line items** per financial statement
- **Comparative periods** (Current vs Prior)
- **Actual dates** in headers (not "Current"/"Prior")
- **YoY changes** with percentages

### Five Main Tabs
1. **Query** - Enter analysis requests
2. **Comprehensive Report** - Full 3-5 page analysis
3. **Financial Statements** - Complete Balance Sheet, Income Statement, Cash Flow
4. **Financial Metrics** - Ratios with YoY comparison
5. **Data Verification** - Quality assurance report

## 🛠️ Requirements

Already installed if you ran the setup:
- ✅ Python 3.9+
- ✅ Virtual environment (.venv)
- ✅ Gradio 4.0+
- ✅ All dependencies

## ⚡ Pro Tips

1. **Use Templates First** - They're pre-tested and work great
2. **Be Specific** - Include company name and period (e.g., "Q3 2025")
3. **Wait Patiently** - Analysis takes 30-60 seconds (it's doing real work!)
4. **Check Verification Tab** - Confirms data quality
5. **Download Reports** - Save as Markdown for later

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'gradio'"
```bash
# Install gradio
.venv/bin/pip install gradio
```

### "Port 7860 already in use"
```bash
# Find and kill the process
lsof -i :7860
kill -9 <PID>

# Or use a different port
.venv/bin/python -m financial_research_agent.web_app --server-port 8080
```

### "Connection refused" or "Can't access from network"
```bash
# Allow network access
.venv/bin/python launch_web_app.py --server-name 0.0.0.0
# Then access from: http://<your-ip>:7860
```

## 📚 More Information

- **Full Guide:** [WEB_APP_GUIDE.md](WEB_APP_GUIDE.md)
- **Database Options:** [DATABASE_INTEGRATION.md](DATABASE_INTEGRATION.md)
- **Implementation Details:** [WEB_INTERFACE_SUMMARY.md](WEB_INTERFACE_SUMMARY.md)

## 🎯 What's Next?

After trying the interface:

**Phase 2 Options:**
- Dashboard with charts
- PDF export
- Search previous analyses
- Company comparisons

**Database Integration:**
- Save query history
- Cache financial data
- Enable search

See [DATABASE_INTEGRATION.md](DATABASE_INTEGRATION.md) for guidance on when/how to add a database.

---

**Questions?** Check [WEB_APP_GUIDE.md](WEB_APP_GUIDE.md) for detailed documentation.
