#!/usr/bin/env python3
"""
Quick test to validate SQLite cache is working.
Run this BEFORE implementing the full cache system.

Usage:
    uv run python test_cache_quick.py
"""

import sqlite3
from pathlib import Path
from datetime import datetime

def test_sqlite_cache():
    """Test basic SQLite functionality for SEC cache."""
    
    print("🔧 Testing SQLite Cache Setup...")
    print("=" * 60)
    
    # 1. Create cache directory
    cache_dir = Path("data/sec_cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created cache directory: {cache_dir}")
    
    # 2. Create test database
    db_path = cache_dir / "test_financials.db"
    
    # Remove if exists (fresh start)
    if db_path.exists():
        db_path.unlink()
        print(f"🗑️  Removed old test database")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    print(f"✅ Connected to database: {db_path}")
    
    # 3. Create minimal schema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS filings_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            form_type TEXT NOT NULL,
            filing_date TEXT NOT NULL,
            accession_number TEXT,
            is_foreign INTEGER DEFAULT 0,
            accounting_standard TEXT DEFAULT 'US-GAAP',
            cached_at TEXT NOT NULL,
            last_accessed TEXT NOT NULL,
            UNIQUE(ticker, form_type, filing_date)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS balance_sheet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filing_id INTEGER NOT NULL,
            ticker TEXT NOT NULL,
            filing_date TEXT NOT NULL,
            concept TEXT NOT NULL,
            label TEXT NOT NULL,
            value REAL,
            currency TEXT DEFAULT 'USD',
            FOREIGN KEY (filing_id) REFERENCES filings_metadata(id)
        )
    """)
    
    print("✅ Created tables: filings_metadata, balance_sheet")
    
    # 4. Test insert filing metadata
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO filings_metadata 
        (ticker, form_type, filing_date, accession_number, is_foreign, accounting_standard, cached_at, last_accessed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ("AAPL", "10-K", "2024-11-01", "0000320193-24-000123", 0, "US-GAAP", now, now))
    
    filing_id = cursor.lastrowid
    print(f"✅ Inserted filing metadata (id: {filing_id}) for AAPL 10-K")
    
    # 5. Test insert balance sheet items
    balance_sheet_items = [
        ("Assets", "Total Assets", 352755000000),
        ("AssetsCurrent", "Current Assets", 143566000000),
        ("Liabilities", "Total Liabilities", 279414000000),
        ("LiabilitiesCurrent", "Current Liabilities", 133973000000),
        ("StockholdersEquity", "Stockholders Equity", 73341000000),
    ]
    
    for concept, label, value in balance_sheet_items:
        cursor.execute("""
            INSERT INTO balance_sheet 
            (filing_id, ticker, filing_date, concept, label, value, currency)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (filing_id, "AAPL", "2024-11-01", concept, label, value, "USD"))
    
    print(f"✅ Inserted {len(balance_sheet_items)} balance sheet items")
    
    conn.commit()
    
    # 6. Test retrieval
    cursor.execute("""
        SELECT m.ticker, m.form_type, m.filing_date, b.label, b.value
        FROM filings_metadata m
        JOIN balance_sheet b ON m.id = b.filing_id
        WHERE m.ticker = 'AAPL'
        ORDER BY b.value DESC
        LIMIT 3
    """)
    
    results = cursor.fetchall()
    print("\n📊 Top 3 Balance Sheet Items for AAPL:")
    for ticker, form, date, label, value in results:
        print(f"   {label}: ${value:,.0f}")
    
    # 7. Verify balance sheet equation
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN concept = 'Assets' THEN value ELSE 0 END) as total_assets,
            SUM(CASE WHEN concept = 'Liabilities' THEN value ELSE 0 END) as total_liabilities,
            SUM(CASE WHEN concept = 'StockholdersEquity' THEN value ELSE 0 END) as equity
        FROM balance_sheet
        WHERE ticker = 'AAPL' AND filing_date = '2024-11-01'
    """)
    
    assets, liabilities, equity = cursor.fetchone()
    
    print(f"\n🧮 Balance Sheet Equation Check:")
    print(f"   Assets:              ${assets:,.0f}")
    print(f"   Liabilities + Equity: ${liabilities + equity:,.0f}")
    print(f"   Difference:          ${abs(assets - (liabilities + equity)):,.0f}")
    
    if abs(assets - (liabilities + equity)) < 1000:  # Allow small rounding
        print("   ✅ Balance sheet balances!")
    else:
        print("   ⚠️  Balance sheet doesn't balance (expected for test data)")
    
    # 8. Check database size
    db_size = db_path.stat().st_size / 1024  # KB
    print(f"\n💾 Database size: {db_size:.1f} KB")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Cache is working! Database created successfully.")
    print(f"📁 Location: {db_path}")
    print("\nNext steps:")
    print("1. Run test_20f_quick.py to test 20-F support")
    print("2. Run test_speed.py to measure cache performance")
    print("3. Start implementing full cache in Phase 1")
    
    return True

if __name__ == "__main__":
    try:
        test_sqlite_cache()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
