# Financial Research Agent - Web Interface Guide

## 🚀 Quick Start

### 1. Launch the Web Application

```bash
python launch_web_app.py
```

Or directly:

```bash
python -m financial_research_agent.web_app
```

The interface will open automatically at: **http://localhost:7860**

### 2. Using the Interface

#### Tab 1: Query & Analysis Setup 🔍

1. **Enter your query** or click a quick template:
   - "Analyze Tesla's Q3 2025 financial performance"
   - "Evaluate Microsoft's financial health and stability"
   - "Compare Google and Microsoft's financial performance"

2. **Click "Generate Analysis"** button

3. **Watch progress** - Real-time updates as the analysis runs:
   - Extracting financial data from SEC EDGAR...
   - Analyzing financial statements...
   - Calculating metrics...

4. **Results appear** in the other tabs automatically

#### Tab 2: Comprehensive Report 📄

- **Full 3-5 page research report** with:
  - Executive Summary
  - Financial Performance Analysis
  - Risk Assessment
  - Forward-Looking Indicators
  - Synthesis and Recommendations

- **Download Options:**
  - Markdown format (for editing)
  - PDF format (coming soon)

#### Tab 3: Financial Statements 💰

- **Complete financial statements** from SEC EDGAR:
  - Consolidated Balance Sheet
  - Consolidated Statement of Operations
  - Consolidated Statement of Cash Flows

- **Features:**
  - Side-by-side period comparison
  - Human-readable labels (not technical XBRL names)
  - Actual report dates (e.g., 2025-09-30)
  - Complete line items (40-50+ items per statement)

#### Tab 4: Financial Metrics & Ratios 📈

- **Comprehensive ratio analysis** with YoY comparison:
  - **Liquidity Ratios:** Current, Quick, Cash
  - **Solvency Ratios:** Debt-to-Equity, Debt-to-Assets, Equity Ratio
  - **Profitability Ratios:** Gross/Operating/Net Margins, ROA, ROE
  - **Efficiency Ratios:** Asset Turnover, Inventory Turnover, DSO

- **Each ratio shows:**
  - Current Period (with actual date)
  - Prior Period (with actual date)
  - Absolute Change
  - Percentage Change
  - Trend indicator (↑/↓/→)

#### Tab 5: Data Verification ✅

- **Quality assurance report** showing:
  - ✅ All three statements present
  - ✅ Balance sheet equation validated
  - ✅ Line item count statistics
  - ✅ Comparative period data complete
  - ✅ Critical line items present

- **Source validation:**
  - SEC EDGAR accession numbers
  - XBRL precision guarantee
  - Filing dates and references

## 📊 Features

### Phase 1 (Current)

✅ **Query Templates** - Pre-built queries for common analyses
✅ **Comprehensive Reports** - Full investment-grade analysis
✅ **Financial Statements** - Complete SEC EDGAR data
✅ **Financial Metrics** - Ratios with YoY comparison
✅ **Data Verification** - Quality assurance
✅ **Morningstar Theme** - Professional styling
✅ **Progress Indicators** - Real-time status updates

### Coming in Phase 2

🔜 **Dashboard Tab** - Key metrics visualization
🔜 **Interactive Charts** - Plotly-powered visualizations
🔜 **Export Options** - PDF and Excel formats
🔜 **SEC Filings Search** - Browse and search filings
🔜 **History** - Access previous analyses

### Coming in Phase 3

🔜 **Company Comparison** - Side-by-side analysis
🔜 **Industry Benchmarking** - Compare against peers
🔜 **Custom Reports** - Select which sections to include

## 🎨 Theme & Design

The interface uses a **Morningstar-inspired** professional theme:

- **Colors:**
  - Primary Blue: #0066cc (trust, stability)
  - Background: #f5f7fa (clean, minimal)
  - Borders: #e0e4e8 (subtle separation)

- **Typography:**
  - Sans-serif: Inter, system-ui
  - Monospace: IBM Plex Mono

- **Layout:**
  - Clean white cards
  - Generous spacing
  - Clear visual hierarchy
  - Mobile-responsive (built-in with Gradio)

## 🔧 Configuration

### Port Configuration

Default port is **7860**. To change:

```python
# In web_app.py, modify launch settings:
launch_settings = {
    'server_port': 8080,  # Change to your preferred port
}
```

### Advanced Options

```bash
# Share publicly (creates temporary public URL)
python launch_web_app.py --share

# Custom port
python launch_web_app.py --server-port 8080

# Debug mode
python launch_web_app.py --debug
```

## 💾 Data Storage

### Current Behavior

- Reports are saved in `financial_research_agent/output/YYYYMMDD_HHMMSS/`
- Each session creates a new timestamped directory
- Files saved:
  - `03_financial_statements.md`
  - `04_financial_metrics.md`
  - `06_final_research_report.md`
  - `data_verification.md`

### Database Integration (Phase 4)

For production use, consider implementing:

1. **SQLite Database** (Simple, embedded)
   ```python
   # Store:
   - Query history
   - Generated reports
   - User preferences
   - Cached financial data
   ```

2. **PostgreSQL** (Production-grade)
   ```python
   # Features:
   - Full-text search on reports
   - Historical trend analysis
   - Multi-user support
   - Report versioning
   ```

3. **Vector Database** (Advanced)
   ```python
   # For semantic search:
   - ChromaDB, Pinecone, or Weaviate
   - Semantic search across reports
   - Find similar companies
   - RAG-based Q&A
   ```

See `DATABASE_INTEGRATION.md` for detailed implementation guide.

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Find process using port 7860
lsof -i :7860

# Kill the process
kill -9 <PID>
```

### Environment Variables Not Loaded

```bash
# Make sure .env file exists
ls -la .env

# Check it contains SEC_EDGAR_USER_AGENT
cat .env
```

### Analysis Fails

1. Check SEC EDGAR user agent is set in `.env`
2. Verify internet connection (accesses SEC.gov)
3. Try a different company (some may have incomplete data)
4. Check console output for detailed error messages

### Gradio Not Installing

```bash
# Install manually
.venv/bin/pip install gradio

# Or use specific version
.venv/bin/pip install gradio==5.49.1
```

## 📝 Examples

### Example 1: Quick Analysis

1. Open http://localhost:7860
2. Click "Tesla Q3 2025 Performance" template
3. Click "Generate Analysis"
4. Switch to "Comprehensive Report" tab to read results

### Example 2: Comparative Analysis

1. Enter: "Compare Apple and Microsoft's Q3 2025 financial performance"
2. Generate analysis
3. Review Financial Metrics tab for side-by-side comparison

### Example 3: Risk Focus

1. Enter: "What are the key financial risks facing Amazon?"
2. Generate analysis
3. Review Comprehensive Report → Risk Assessment section

## 🤝 Contributing

To enhance the web interface:

1. **Add new query templates** - Edit `QUERY_TEMPLATES` in `web_app.py`
2. **Customize theme** - Modify `create_theme()` function
3. **Add new tabs** - Extend the `create_interface()` method

## 📚 Additional Resources

- [Gradio Documentation](https://gradio.app/docs)
- [SEC EDGAR API Guide](financial_research_agent/tools/mcp_tools_guide.py)
- [Financial Metrics Reference](COMPARATIVE_METRICS_UPDATE.md)

## 🎯 Best Practices

1. **Clear Queries** - Be specific about company and period
2. **Wait for Completion** - Analysis takes 30-60 seconds
3. **Review Verification** - Check data quality tab first
4. **Save Important Reports** - Download markdown for archival
5. **Compare Periods** - Look at YoY changes in metrics

---

**Need Help?** Check the [main README](README.md) or open an issue on GitHub.
