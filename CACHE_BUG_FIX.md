# Cache Bug Fix - Missing Financial Statement Processing

## Problem

When financial statements are retrieved from the JSON file cache (`FinancialDataCache`), 
the cached data is missing computed fields that are generated during fresh extraction:

- `yoy_tables` - Year-over-year comparison tables
- `key_metrics` - Extracted key financial metrics

This causes the second run of an analysis to fail or produce incomplete output.

## Root Cause

In `financial_research_agent/manager_enhanced.py` lines 580-718:

```python
# PERFORMANCE: Check cache first
cached_statements = self.cache.get(lookup_key, "financial_statements")
if cached_statements:
    statements_data = cached_statements  # ← Cached data loaded
    
if not cached_statements:
    # Fresh extraction
    statements_data = await extract_financial_data_enhanced(...)
    
    # Generate YoY tables (lines 666-712)
    if 'balance_sheet_df' in statements_data:
        yoy_tables = {}
        # ... YoY generation code ...
        statements_data['yoy_tables'] = yoy_tables  # ← Only added to fresh data!
        
        # Extract key metrics (lines 714-718)
        key_metrics = extract_key_metrics_from_statements(...)
        statements_data['key_metrics'] = key_metrics  # ← Only added to fresh data!
    
    # Cache the data
    self.cache.set(lookup_key, "financial_statements", statements_data)
```

**The issue:** YoY tables and key metrics are only generated when `not cached_statements` is True.
Cached data never gets these fields added, causing downstream code to fail.

## Solution

**Option A: Generate computed fields for cached data** (Recommended)

Move the YoY table and key metrics generation OUTSIDE the `if not cached_statements` block
so it always runs regardless of cache hit/miss:

```python
# PERFORMANCE: Check cache first
cached_statements = self.cache.get(lookup_key, "financial_statements")
if cached_statements:
    self.console.print(f"[dim]✓ Using cached financial data for {lookup_key}[/dim]")
    statements_data = cached_statements

if not cached_statements:
    # Step 1: Use enhanced extraction to get complete financial data with XBRL features
    self.printer.update_item("metrics", f"Extracting financial data for {lookup_key}...")
    
    statements_data = await extract_financial_data_enhanced(
        self.edgar_server,
        lookup_key
    )
    
    # PERFORMANCE: Cache the extracted data
    if statements_data:
        self.cache.set(lookup_key, "financial_statements", statements_data)

# ALWAYS generate YoY tables and key metrics (whether cached or fresh)
if statements_data and 'balance_sheet_df' in statements_data:
    try:
        self.printer.update_item("metrics", "Generating year-over-year comparison tables...")
        
        # Generate YoY tables for each statement
        yoy_tables = {}
        
        # Balance Sheet YoY
        bs_yoy = generate_yoy_comparison_table(
            statements_data['balance_sheet_df'],
            "Balance Sheet",
            key_items=['Assets', 'Total Assets', 'Liabilities', 'Total Liabilities',
                      'Equity', 'Total Equity', "Stockholders' Equity", "Total Stockholders' Equity",
                      'Cash and Cash Equivalents', 'Total Current Assets', 'Total Current Liabilities']
        )
        yoy_tables['balance_sheet'] = bs_yoy
        
        # Income Statement YoY
        is_yoy = generate_yoy_comparison_table(
            statements_data['income_statement_df'],
            "Income Statement",
            key_items=['Revenue', 'Revenues', 'Total Revenue', 'Net Sales', 'Contract Revenue',
                      'Gross Profit', 'Operating Income', 'Net Income', 'Earnings Per Share']
        )
        yoy_tables['income_statement'] = is_yoy
        
        # Cash Flow Statement YoY
        cf_yoy = generate_yoy_comparison_table(
            statements_data['cash_flow_statement_df'],
            "Cash Flow Statement",
            key_items=['Net Cash Provided by Operating Activities', 'Net Cash From Operating Activities',
                      'Capital Expenditures', 'Payments for Property, Plant and Equipment',
                      'Free Cash Flow', 'Dividends Paid', 'Stock Repurchases']
        )
        yoy_tables['cash_flow'] = cf_yoy
        
        # Store YoY tables for inclusion in 03_financial_statements.md
        statements_data['yoy_tables'] = yoy_tables
        self.console.print("[green]✓ YoY comparison tables generated[/green]")
        
        # Extract key metrics using enhanced function
        key_metrics = extract_key_metrics_from_statements(
            statements_data['balance_sheet_df'],
            statements_data['income_statement_df'],
            statements_data['cash_flow_statement_df']
        )
        statements_data['key_metrics'] = key_metrics
        
        if key_metrics.get('current'):
            self.console.print(f"[dim]  Key metrics extracted: Revenue=${key_metrics['current'].get('revenue', 0)/1e9:.1f}B, FCF=${key_metrics['current'].get('free_cash_flow', 0)/1e9:.1f}B[/dim]")
            
    except Exception as e:
        self.console.print(f"[yellow]Warning: YoY table generation failed: {e}[/yellow]")
        import traceback
        traceback.print_exc()
```

**Option B: Store computed fields in cache** (Alternative)

Generate YoY tables and key metrics before caching, so the cached data already has them:

```python
if not cached_statements:
    # Extract data
    statements_data = await extract_financial_data_enhanced(...)
    
    # Generate YoY tables and metrics BEFORE caching
    if statements_data and 'balance_sheet_df' in statements_data:
        # ... generate yoy_tables ...
        # ... extract key_metrics ...
        statements_data['yoy_tables'] = yoy_tables
        statements_data['key_metrics'] = key_metrics
    
    # Now cache the complete data with computed fields
    self.cache.set(lookup_key, "financial_statements", statements_data)
```

**Option C: Clear the cache and use fresh data** (Quick workaround)

Delete the cache files to force fresh extraction every time:

```bash
rm -rf financial_research_agent/cache/*.json
```

## Recommended Fix

**Option A is best** because:
- ✅ Handles both cache hit and cache miss correctly
- ✅ Avoids storing large computed DataFrames in cache
- ✅ Cache only stores raw extracted data
- ✅ Computed fields are generated on-demand

## Implementation

Replace lines 580-718 in `financial_research_agent/manager_enhanced.py` with the Option A code above.

## Testing

After applying the fix:

1. Clear existing cache: `rm -rf financial_research_agent/cache/*.json`
2. Run first analysis: `python -m financial_research_agent.main_enhanced` (fresh extraction)
3. Run second analysis on same company (should use cache and work correctly)
4. Verify both runs produce complete financial statements with YoY tables

## Related Files

- `financial_research_agent/manager_enhanced.py` - Contains the bug
- `financial_research_agent/cache/data_cache.py` - Simple JSON file cache
- `financial_research_agent/cache/sec_financial_cache.py` - SQLite cache (not used yet)

## Note on SQLite Cache

The SQLite cache (`SecFinancialCache`) was built in Phase 1 but is NOT integrated into the application yet.
This is Task 2.4 - integrating `FinancialDataManager` which uses the SQLite cache properly.

Once Task 2.4 is complete, this JSON cache bug will be superseded by the proper SQLite caching system.
