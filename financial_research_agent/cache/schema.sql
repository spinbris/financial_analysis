-- SQLite Schema for SEC Financial Data Cache
-- Version: 1.0
-- Created: 2024-11-24

-- ============================================================
-- FILINGS METADATA
-- ============================================================
-- Stores metadata about cached SEC filings
CREATE TABLE IF NOT EXISTS filings_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    cik TEXT,
    company_name TEXT,
    form_type TEXT NOT NULL,  -- 10-K, 10-Q, 20-F, 6-K
    filing_date TEXT NOT NULL,  -- YYYY-MM-DD
    fiscal_year INTEGER,
    fiscal_period TEXT,  -- FY, Q1, Q2, Q3, Q4
    accession_number TEXT,
    filing_url TEXT,
    is_foreign INTEGER DEFAULT 0,  -- 0=US, 1=Foreign
    accounting_standard TEXT DEFAULT 'US-GAAP',  -- US-GAAP or IFRS
    cached_at TEXT NOT NULL,  -- ISO format timestamp
    last_accessed TEXT NOT NULL,  -- ISO format timestamp
    data_quality_score REAL DEFAULT 1.0,  -- 0.0 to 1.0
    UNIQUE(ticker, form_type, filing_date)
);

CREATE INDEX IF NOT EXISTS idx_filings_ticker ON filings_metadata(ticker);
CREATE INDEX IF NOT EXISTS idx_filings_date ON filings_metadata(filing_date DESC);
CREATE INDEX IF NOT EXISTS idx_filings_ticker_date ON filings_metadata(ticker, filing_date DESC);
CREATE INDEX IF NOT EXISTS idx_filings_form_type ON filings_metadata(form_type);
CREATE INDEX IF NOT EXISTS idx_filings_foreign ON filings_metadata(is_foreign);

-- ============================================================
-- BALANCE SHEET
-- ============================================================
-- Stores balance sheet line items
CREATE TABLE IF NOT EXISTS balance_sheet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filing_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    filing_date TEXT NOT NULL,
    concept TEXT NOT NULL,  -- XBRL concept name
    label TEXT NOT NULL,  -- Human-readable label
    value REAL,  -- Numerical value
    currency TEXT DEFAULT 'USD',
    unit TEXT DEFAULT 'shares',  -- shares, USD, etc.
    decimals INTEGER,
    context_ref TEXT,  -- XBRL context
    is_abstract INTEGER DEFAULT 0,  -- 1 if section header
    level INTEGER DEFAULT 0,  -- Hierarchy level (0=top)
    parent_concept TEXT,  -- Parent in hierarchy
    FOREIGN KEY (filing_id) REFERENCES filings_metadata(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_bs_filing ON balance_sheet(filing_id);
CREATE INDEX IF NOT EXISTS idx_bs_ticker_date ON balance_sheet(ticker, filing_date DESC);
CREATE INDEX IF NOT EXISTS idx_bs_concept ON balance_sheet(concept);
CREATE INDEX IF NOT EXISTS idx_bs_label ON balance_sheet(label);

-- ============================================================
-- INCOME STATEMENT
-- ============================================================
-- Stores income statement line items
CREATE TABLE IF NOT EXISTS income_statement (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filing_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    filing_date TEXT NOT NULL,
    concept TEXT NOT NULL,
    label TEXT NOT NULL,
    value REAL,
    currency TEXT DEFAULT 'USD',
    unit TEXT DEFAULT 'shares',
    decimals INTEGER,
    context_ref TEXT,
    is_abstract INTEGER DEFAULT 0,
    level INTEGER DEFAULT 0,
    parent_concept TEXT,
    FOREIGN KEY (filing_id) REFERENCES filings_metadata(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_is_filing ON income_statement(filing_id);
CREATE INDEX IF NOT EXISTS idx_is_ticker_date ON income_statement(ticker, filing_date DESC);
CREATE INDEX IF NOT EXISTS idx_is_concept ON income_statement(concept);
CREATE INDEX IF NOT EXISTS idx_is_label ON income_statement(label);

-- ============================================================
-- CASH FLOW STATEMENT
-- ============================================================
-- Stores cash flow statement line items
CREATE TABLE IF NOT EXISTS cash_flow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filing_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    filing_date TEXT NOT NULL,
    concept TEXT NOT NULL,
    label TEXT NOT NULL,
    value REAL,
    currency TEXT DEFAULT 'USD',
    unit TEXT DEFAULT 'shares',
    decimals INTEGER,
    context_ref TEXT,
    is_abstract INTEGER DEFAULT 0,
    level INTEGER DEFAULT 0,
    parent_concept TEXT,
    FOREIGN KEY (filing_id) REFERENCES filings_metadata(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_cf_filing ON cash_flow(filing_id);
CREATE INDEX IF NOT EXISTS idx_cf_ticker_date ON cash_flow(ticker, filing_date DESC);
CREATE INDEX IF NOT EXISTS idx_cf_concept ON cash_flow(concept);
CREATE INDEX IF NOT EXISTS idx_cf_label ON cash_flow(label);

-- ============================================================
-- FINANCIAL RATIOS
-- ============================================================
-- Stores calculated financial ratios
CREATE TABLE IF NOT EXISTS financial_ratios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filing_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    filing_date TEXT NOT NULL,
    ratio_category TEXT NOT NULL,  -- profitability, liquidity, leverage, efficiency, cash_flow
    ratio_name TEXT NOT NULL,
    ratio_value REAL,
    calculated_at TEXT NOT NULL,
    FOREIGN KEY (filing_id) REFERENCES filings_metadata(id) ON DELETE CASCADE,
    UNIQUE(filing_id, ratio_category, ratio_name)
);

CREATE INDEX IF NOT EXISTS idx_ratios_filing ON financial_ratios(filing_id);
CREATE INDEX IF NOT EXISTS idx_ratios_ticker_date ON financial_ratios(ticker, filing_date DESC);
CREATE INDEX IF NOT EXISTS idx_ratios_category ON financial_ratios(ratio_category);

-- ============================================================
-- SEGMENT DATA
-- ============================================================
-- Stores business segment information
CREATE TABLE IF NOT EXISTS segment_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filing_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    filing_date TEXT NOT NULL,
    segment_type TEXT NOT NULL,  -- geographic, product, business_line
    segment_name TEXT NOT NULL,
    metric_name TEXT NOT NULL,  -- revenue, operating_income, assets, etc.
    metric_value REAL,
    currency TEXT DEFAULT 'USD',
    percentage_of_total REAL,
    FOREIGN KEY (filing_id) REFERENCES filings_metadata(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_segment_filing ON segment_data(filing_id);
CREATE INDEX IF NOT EXISTS idx_segment_ticker_date ON segment_data(ticker, filing_date DESC);
CREATE INDEX IF NOT EXISTS idx_segment_type ON segment_data(segment_type);

-- ============================================================
-- CACHE STATISTICS
-- ============================================================
-- Tracks cache usage and performance
CREATE TABLE IF NOT EXISTS cache_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_date TEXT NOT NULL,  -- YYYY-MM-DD
    total_filings INTEGER DEFAULT 0,
    total_us_filings INTEGER DEFAULT 0,
    total_foreign_filings INTEGER DEFAULT 0,
    total_companies INTEGER DEFAULT 0,
    cache_hits INTEGER DEFAULT 0,
    cache_misses INTEGER DEFAULT 0,
    average_retrieval_time_ms REAL DEFAULT 0.0,
    database_size_mb REAL DEFAULT 0.0,
    UNIQUE(stat_date)
);

-- ============================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================

-- Latest filing for each company
CREATE VIEW IF NOT EXISTS latest_filings AS
SELECT 
    m.ticker,
    m.company_name,
    m.form_type,
    m.filing_date,
    m.is_foreign,
    m.accounting_standard,
    m.id as filing_id
FROM filings_metadata m
INNER JOIN (
    SELECT ticker, MAX(filing_date) as max_date
    FROM filings_metadata
    GROUP BY ticker
) latest ON m.ticker = latest.ticker AND m.filing_date = latest.max_date;

-- Complete balance sheet with metadata
CREATE VIEW IF NOT EXISTS balance_sheet_complete AS
SELECT 
    m.ticker,
    m.company_name,
    m.filing_date,
    m.form_type,
    b.concept,
    b.label,
    b.value,
    b.currency,
    b.level,
    b.is_abstract
FROM balance_sheet b
JOIN filings_metadata m ON b.filing_id = m.id
ORDER BY m.ticker, m.filing_date DESC, b.level, b.id;

-- ============================================================
-- INITIALIZATION COMPLETE
-- ============================================================