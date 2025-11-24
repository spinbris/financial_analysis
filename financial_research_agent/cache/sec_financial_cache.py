"""
SQLite-based cache for SEC financial data.

This module provides fast caching of EDGAR filings including:
- Balance sheets
- Income statements
- Cash flow statements
- Financial ratios
- Segment data

Supports both US (10-K/10-Q) and foreign (20-F/6-K) companies.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from edgar import Company, Filing, set_identity
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set EDGAR identity
edgar_identity = os.getenv("EDGAR_IDENTITY") or os.getenv("SEC_EDGAR_USER_AGENT")
if edgar_identity:
    set_identity(edgar_identity)
else:
    set_identity("FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)")


logger = logging.getLogger(__name__)


class SecFinancialCache:
    """
    SQLite cache for SEC financial data.

    Features:
    - Fast retrieval (0.01-0.05s vs 3-5s download)
    - Support for 10-K, 10-Q, 20-F, 6-K filings
    - Automatic staleness detection
    - Full-text search across line items
    - Multi-period queries
    """

    def __init__(self, db_path: str = "data/sec_cache/financials.db"):
        """
        Initialize the financial cache.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        logger.info(f"SecFinancialCache initialized: {self.db_path}")

    def _init_database(self):
        """Initialize database with schema if needed."""
        # Check if database exists and has tables
        if not self.db_path.exists():
            logger.info("Creating new database...")
            self._create_schema()
        else:
            # Verify schema exists
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='filings_metadata'
            """)
            if not cursor.fetchone():
                logger.warning("Database exists but schema missing. Creating schema...")
                self._create_schema()
            conn.close()

    def _create_schema(self):
        """Create database schema from schema.sql."""
        schema_path = Path(__file__).parent / "schema.sql"

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        conn = self._get_connection()
        with open(schema_path, "r") as f:
            schema_sql = f.read()
            conn.executescript(schema_sql)
        conn.commit()
        conn.close()

        logger.info("Database schema created successfully")

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with optimizations."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Access columns by name

        # Performance optimizations
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        conn.execute("PRAGMA synchronous=NORMAL")  # Faster writes
        conn.execute("PRAGMA cache_size=10000")  # 10MB cache
        conn.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp tables

        return conn


    def _cache_filing_metadata(
        self,
        conn: sqlite3.Connection,
        ticker: str,
        filing_data: Dict[str, Any],
        is_foreign: bool,
        accounting_standard: str,
    ) -> int:
        """
        Cache filing metadata.

        Args:
            conn: Database connection
            ticker: Stock ticker
            filing_data: Filing information from edgartools
            is_foreign: Whether company is foreign issuer
            accounting_standard: US-GAAP or IFRS

        Returns:
            filing_id: Database ID of inserted filing
        """
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT OR REPLACE INTO filings_metadata (
                ticker,
                cik,
                company_name,
                form_type,
                filing_date,
                fiscal_year,
                fiscal_period,
                accession_number,
                filing_url,
                is_foreign,
                accounting_standard,
                cached_at,
                last_accessed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                ticker.upper(),
                filing_data.get("cik"),
                filing_data.get("company_name"),
                filing_data.get("form"),
                filing_data.get("filing_date"),
                filing_data.get("fiscal_year"),
                filing_data.get(
                    "fiscal_period",
                    "FY" if filing_data.get("form") in ["10-K", "20-F"] else None,
                ),
                filing_data.get("accession_number"),
                filing_data.get("filing_url"),
                1 if is_foreign else 0,
                accounting_standard,
                now,
                now,
            ),
        )

        # Persist the insert immediately to ensure lastrowid is stable across connections
        conn.commit()

        filing_id = cursor.lastrowid

        logger.info(
            f"Cached filing metadata: {ticker} {filing_data.get('form')} (id={filing_id})"
        )

        return filing_id


    def _cache_statement(
        self,
        conn: sqlite3.Connection,
        filing_id: int,
        ticker: str,
        filing_date: str,
        statement_type: str,
        statement_data: Any
    ) -> int:
        """
        Cache a financial statement (balance sheet, income, or cash flow).
        
        EdgarTools 4.x returns statements as dicts with 'data' key containing line items.
        """
        cursor = conn.cursor()
        
        # Map statement type to table name
        table_map = {
            'balance': 'balance_sheet',
            'income': 'income_statement',
            'cash_flow': 'cash_flow'
        }
        
        table_name = table_map.get(statement_type)
        if not table_name:
            raise ValueError(f"Invalid statement type: {statement_type}")
        
        items_cached = 0
        
        try:
            # EdgarTools 4.x format: dict with 'data' key
            if isinstance(statement_data, dict) and 'data' in statement_data:
                line_items = statement_data['data']
                
                for item in line_items:
                    # Skip abstract items (headers)
                    if item.get('is_abstract', False):
                        continue
                    
                    concept = item.get('concept', 'unknown')
                    label = item.get('label', concept)
                    
                    # Get the most recent value from 'values' dict
                    values = item.get('values', {})
                    if not values:
                        continue
                    
                    # Get the first (most recent) value
                    # Keys are like 'instant_2025-09-27' or 'duration_...'
                    for period_key, value in values.items():
                        # Skip empty values
                        if value == '' or value is None:
                            continue
                        
                        # Get units
                        units = item.get('units', {})
                        unit = units.get(period_key, 'usd')
                        
                        try:
                            cursor.execute(f"""
                                INSERT INTO {table_name} (
                                    filing_id,
                                    ticker,
                                    filing_date,
                                    concept,
                                    label,
                                    value,
                                    currency,
                                    unit,
                                    level
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                filing_id,
                                ticker.upper(),
                                filing_date,
                                concept,
                                label,
                                float(value) if value is not None else None,
                                'USD',
                                unit,
                                item.get('level', 0)
                            ))
                            items_cached += 1
                        except (ValueError, TypeError) as e:
                            # Skip items that can't be converted to float
                            continue
                        
                        # Only cache the first (most recent) period
                        break
            
            logger.info(f"Cached {items_cached} items for {statement_type} statement")
            
        except Exception as e:
            logger.error(f"Error caching {statement_type} statement: {e}")
            raise
        
        return items_cached


    def cache_filing(
        self, 
        ticker: str, 
        filing_data: Dict[str, Any]
    ) -> int:
        """Cache a complete SEC filing."""
        from edgar import Company
        
        conn = self._get_connection()
        
        try:
            is_foreign = filing_data.get('is_foreign', False)
            accounting_standard = filing_data.get('accounting_standard', 'US-GAAP')
            
            filing_id = self._cache_filing_metadata(
                conn,
                ticker,
                filing_data,
                is_foreign,
                accounting_standard
            )
            
            print(f"\n🔍 Debug: Getting filing object for {ticker}")
            
            company = Company(ticker)
            form_type = filing_data.get('form')
            filing_date = filing_data.get('filing_date')
            
            print(f"   Looking for {form_type} on {filing_date}")
            
            filings_list = company.get_filings(form=form_type)
            print(f"   Found {len(filings_list)} {form_type} filings")
            
            filing_obj = None
            for filing in filings_list:
                print(f"   Checking filing from {filing.filing_date}")
                if str(filing.filing_date) == str(filing_date):
                    filing_obj = filing
                    print(f"   ✅ Found matching filing!")
                    break
            
            if filing_obj is None:
                print(f"   ❌ Could not find matching filing")
                conn.commit()
                return filing_id
            
            # Check what methods are available
            print(f"   Filing object type: {type(filing_obj)}")
            print(f"   Available methods: {[m for m in dir(filing_obj) if not m.startswith('_')]}")
            
            # Try different ways to get financials
            financials = None
                
            try:
                xbrl = filing_obj.xbrl()
                
                if xbrl:
                    print(f"   ✅ Got XBRL object")
                    
                    # Get Balance Sheet
                    bs = xbrl.get_statement_by_type('BalanceSheet')
                    if bs and isinstance(bs, dict) and 'data' in bs:
                        items = self._cache_statement(conn, filing_id, ticker, filing_date, 'balance', bs)
                        print(f"   ✅ Cached {items} balance sheet items")
                    
                    # Get Income Statement
                    inc = xbrl.get_statement_by_type('IncomeStatement')
                    if inc and isinstance(inc, dict) and 'data' in inc:
                        items = self._cache_statement(conn, filing_id, ticker, filing_date, 'income', inc)
                        print(f"   ✅ Cached {items} income statement items")
                    
                    # Get Cash Flow Statement
                    cf = xbrl.get_statement_by_type('CashFlowStatement')
                    if cf and isinstance(cf, dict) and 'data' in cf:
                        items = self._cache_statement(conn, filing_id, ticker, filing_date, 'cash_flow', cf)
                        print(f"   ✅ Cached {items} cash flow items")
    
            except Exception as e:
                print(f"   ❌ XBRL extraction error: {e}")
            
            conn.commit()
            return filing_id
            
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
   


    def get_cached_financials(
        self, ticker: str, periods: int = 4
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached financial data for a company.

        Args:
            ticker: Stock ticker symbol
            periods: Number of periods to retrieve

        Returns:
            Dict with complete financial data or None if not cached
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Get filing metadata
            cursor.execute(
                """
                SELECT *
                FROM filings_metadata
                WHERE ticker = ?
                ORDER BY filing_date DESC
                LIMIT ?
            """,
                (ticker.upper(), periods),
            )

            filings = [dict(row) for row in cursor.fetchall()]

            if not filings:
                return None

            # Get financial statements for each filing
            result = {"ticker": ticker.upper(), "periods": []}

            for filing in filings:
                filing_id = filing["id"]

                # Get balance sheet
                cursor.execute(
                    """
                    SELECT concept, label, value, currency
                    FROM balance_sheet
                    WHERE filing_id = ?
                    ORDER BY id
                """,
                    (filing_id,),
                )
                balance_sheet = [dict(row) for row in cursor.fetchall()]

                # Get income statement
                cursor.execute(
                    """
                    SELECT concept, label, value, currency
                    FROM income_statement
                    WHERE filing_id = ?
                    ORDER BY id
                """,
                    (filing_id,),
                )
                income_statement = [dict(row) for row in cursor.fetchall()]

                # Get cash flow
                cursor.execute(
                    """
                    SELECT concept, label, value, currency
                    FROM cash_flow
                    WHERE filing_id = ?
                    ORDER BY id
                """,
                    (filing_id,),
                )
                cash_flow = [dict(row) for row in cursor.fetchall()]

                # Update last_accessed
                cursor.execute(
                    """
                    UPDATE filings_metadata
                    SET last_accessed = ?
                    WHERE id = ?
                """,
                    (datetime.now().isoformat(), filing_id),
                )

                result["periods"].append(
                    {
                        "filing_date": filing["filing_date"],
                        "form_type": filing["form_type"],
                        "is_foreign": bool(filing["is_foreign"]),
                        "accounting_standard": filing["accounting_standard"],
                        "balance_sheet": balance_sheet,
                        "income_statement": income_statement,
                        "cash_flow": cash_flow,
                    }
                )

            conn.commit()
            conn.close()

            logger.info(f"Retrieved {len(result['periods'])} periods for {ticker}")

            return result

        except Exception as e:
            logger.error(f"Error retrieving cached financials for {ticker}: {e}")
            conn.close()
            return None
        
        
    def cache_company(
        self,
        ticker: str,
        max_filings: int = 4,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Cache a complete company with multiple filings.
        
        Args:
            ticker: Stock ticker symbol
            max_filings: Maximum number of filings to cache (default 4 = 1 annual + 3 quarterly)
            force_refresh: Force re-cache even if data exists
            
        Returns:
            Dict with caching results:
            {
                'ticker': str,
                'filings_cached': int,
                'total_items': int,
                'is_foreign': bool,
                'cache_time_seconds': float
            }
        """
        import time
        start_time = time.time()
        
        # Check if already cached and current
        if not force_refresh:
            status = self.check_cache_status(ticker)
            if status['cached'] and status['current']:
                logger.info(f"{ticker} already cached and current, skipping")
                return {
                    'ticker': ticker,
                    'filings_cached': status['filing_count'],
                    'total_items': self._get_item_count(ticker),
                    'is_foreign': status['is_foreign'],
                    'cache_time_seconds': 0,
                    'from_cache': True
                }
        
        # Get required filings
        try:
            filings_info = self.get_required_filings(ticker)
        except Exception as e:
            logger.error(f"Error getting filings for {ticker}: {e}")
            return {
                'ticker': ticker,
                'filings_cached': 0,
                'total_items': 0,
                'error': str(e),
                'cache_time_seconds': time.time() - start_time
            }
        
        filings_cached = 0
        total_items = 0
        
        # Cache annual filing
        try:
            annual_data = filings_info['annual'].to_dict() if hasattr(filings_info['annual'], 'to_dict') else dict(filings_info['annual'])
            annual_data['is_foreign'] = filings_info['is_foreign']
            annual_data['accounting_standard'] = filings_info['accounting_standard']
            
            filing_id = self.cache_filing(ticker, annual_data)
            if filing_id:
                filings_cached += 1
                total_items += self._get_filing_item_count(filing_id)
                logger.info(f"Cached annual filing for {ticker}")
        except Exception as e:
            logger.error(f"Error caching annual filing for {ticker}: {e}")
        
        # Cache quarterly filings (up to max_filings - 1)
        quarterlies_to_cache = min(len(filings_info['quarterlies']), max_filings - 1)
        
        for i, quarterly in enumerate(filings_info['quarterlies'][:quarterlies_to_cache]):
            try:
                quarterly_data = quarterly.to_dict() if hasattr(quarterly, 'to_dict') else dict(quarterly)
                quarterly_data['is_foreign'] = filings_info['is_foreign']
                quarterly_data['accounting_standard'] = filings_info['accounting_standard']
                
                filing_id = self.cache_filing(ticker, quarterly_data)
                if filing_id:
                    filings_cached += 1
                    total_items += self._get_filing_item_count(filing_id)
                    logger.info(f"Cached quarterly {i+1} for {ticker}")
            except Exception as e:
                logger.error(f"Error caching quarterly {i+1} for {ticker}: {e}")
        
        elapsed = time.time() - start_time
        
        result = {
            'ticker': ticker,
            'filings_cached': filings_cached,
            'total_items': total_items,
            'is_foreign': filings_info['is_foreign'],
            'cache_time_seconds': round(elapsed, 2),
            'from_cache': False
        }
        
        logger.info(f"Cached {ticker}: {filings_cached} filings, {total_items} items in {elapsed:.2f}s")
        
        return result


    def _get_item_count(self, ticker: str) -> int:
        """Get total number of cached items for a ticker."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        total = 0
        for table in ['balance_sheet', 'income_statement', 'cash_flow']:
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE ticker = ?", (ticker.upper(),))
            total += cursor.fetchone()[0]
        
        conn.close()
        return total


    def _get_filing_item_count(self, filing_id: int) -> int:
        """Get total number of items for a specific filing."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        total = 0
        for table in ['balance_sheet', 'income_statement', 'cash_flow']:
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE filing_id = ?", (filing_id,))
            total += cursor.fetchone()[0]
        
        conn.close()
        return total    
            
            

    # ========================================
    # CORE METHODS - Implement next
    # ========================================

    def check_cache_status(self, ticker: str, max_age_days: int = 7) -> Dict[str, Any]:
        """
        Check if ticker is cached and if cache is current.

        Args:
            ticker: Stock ticker symbol
            max_age_days: Maximum age in days before cache is stale

        Returns:
            Dict with cache status information:
            {
                'cached': bool,
                'current': bool,
                'needs_update': bool,
                'cache_age_days': int,
                'filing_count': int,
                'latest_filing_date': str,
                'is_foreign': bool
            }
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Check if ticker exists in cache
        cursor.execute(
            """
            SELECT 
                COUNT(*) as filing_count,
                MAX(filing_date) as latest_date,
                MAX(cached_at) as last_cached,
                MAX(is_foreign) as is_foreign
            FROM filings_metadata
            WHERE ticker = ?
        """,
            (ticker.upper(),),
        )

        result = cursor.fetchone()
        filing_count = result["filing_count"]
        latest_date = result["latest_date"]
        last_cached = result["last_cached"]
        is_foreign = (
            bool(result["is_foreign"]) if result["is_foreign"] is not None else False
        )

        conn.close()

        # Not cached at all
        if filing_count == 0:
            return {
                "cached": False,
                "current": False,
                "needs_update": True,
                "cache_age_days": None,
                "filing_count": 0,
                "latest_filing_date": None,
                "is_foreign": False,
            }

        # Calculate cache age
        cached_datetime = datetime.fromisoformat(last_cached)
        age_days = (datetime.now() - cached_datetime).days

        # Check if current (within max_age_days)
        is_current = age_days <= max_age_days

        return {
            "cached": True,
            "current": is_current,
            "needs_update": not is_current,
            "cache_age_days": age_days,
            "filing_count": filing_count,
            "latest_filing_date": latest_date,
            "is_foreign": is_foreign,
        }

    
    def search_line_items(
        self,
        search_term: str,
        ticker: Optional[str] = None,
        statement_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search for line items across financial statements.

        Args:
            ticker: Stock ticker symbol
            search_term: Term to search for (in label or concept)
            statement: Which statement(s) to search (all/balance/income/cash_flow)

        Returns:
            List of matching line items
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        results = []

        # Tables to search
        if statement_type:
            table_map = {
                'balance': 'balance_sheet',
                'income': 'income_statement',
                'cash_flow': 'cash_flow'
            }
            tables = [table_map.get(statement_type)]
            if tables[0] is None:
                return []
        else:
            tables = ['balance_sheet', 'income_statement', 'cash_flow']

        for table in tables:
            query = f"""
                SELECT 
                    '{table}' as statement_type,
                    ticker,
                    filing_date,
                    concept,
                    label,
                    value,
                    currency
                FROM {table}
                WHERE (label LIKE ? OR concept LIKE ?)
            """
            params = [f'%{search_term}%', f'%{search_term}%']

            if ticker:
                query += " AND ticker = ?"
                params.append(ticker.upper())

            query += f" ORDER BY filing_date DESC LIMIT {limit}"

            cursor.execute(query, params)

            for row in cursor.fetchall():
                results.append({
                    'statement_type': row['statement_type'],
                    'ticker': row['ticker'],
                    'filing_date': row['filing_date'],
                    'concept': row['concept'],
                    'label': row['label'],
                    'value': row['value'],
                    'currency': row['currency']
                })

        conn.close()

        # Sort by relevance then by date
        def sort_key(item):
            exact = search_term.lower() in item['label'].lower()
            return (not exact, item['filing_date'])

        results.sort(key=sort_key, reverse=True)

        return results[:limit]
    
    
    def get_specific_items(
        self,
        ticker: str,
        items: List[str]
    ) -> Dict[str, Optional[float]]:
        """
        Get specific financial items by concept OR label.
    
        Args:
            ticker: Stock ticker symbol
            items: List of concept names OR labels (e.g., ['Total Assets', 'Cash'])
        """
        conn = self._get_connection()
        cursor = conn.cursor()
    
        results = {}
    
        for item in items:
            for table in ['balance_sheet', 'income_statement', 'cash_flow']:
                #search by both concept and label
                cursor.execute(f"""
                    SELECT value, filing_date
                    FROM {table}
                    WHERE ticker = ? 
                    AND (concept = ? OR label LIKE ? OR label LIKE ?)
                    ORDER BY filing_date DESC
                    LIMIT 1
                """, (ticker.upper(), item, item, f'%{item}%'))
                
                row = cursor.fetchone()
                if row:
                    results[item] = row['value']
                    break
            else:
                results[item] = None

        conn.close()
        return results

    def compare_companies(
        self,
        tickers: List[str],
        concepts: List[str]
    ) -> Dict[str, Dict[str, Optional[float]]]:
        """Compare specific metrics across multiple companies."""
        results = {}
        
        for ticker in tickers:
            results[ticker] = self.get_specific_items(ticker, concepts)
        
        return results

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics and health metrics.

        Returns:
            Dict with cache statistics
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get counts
        cursor.execute("SELECT COUNT(*) FROM filings_metadata")
        total_filings = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT ticker) FROM filings_metadata")
        unique_companies = cursor.fetchone()[0]

        cursor.execute("""
            SELECT 
                SUM(CASE WHEN is_foreign = 1 THEN 1 ELSE 0 END) as foreign_count,
                SUM(CASE WHEN is_foreign = 0 THEN 1 ELSE 0 END) as domestic_count
            FROM filings_metadata
        """)
        foreign, domestic = cursor.fetchone()

        # Get database size
        db_size_bytes = self.db_path.stat().st_size
        db_size_mb = db_size_bytes / (1024 * 1024)

        conn.close()

        return {
            "total_filings": total_filings,
            "unique_companies": unique_companies,
            "us_companies": domestic or 0,
            "foreign_companies": foreign or 0,
            "database_size_mb": round(db_size_mb, 2),
            "database_path": str(self.db_path),
        }

    def close(self):
        """Close database connection and cleanup."""
        logger.info("SecFinancialCache closed")

    def get_required_filings(self, ticker: str) -> Dict[str, Any]:
        """
        Determine which filings are required for a ticker.

        Strategy:
        - Get latest annual report (10-K or 20-F)
        - Get subsequent quarterly reports (10-Q or 6-K)
        - Max 3 quarterly reports

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dict with filing requirements:
            {
                'annual': Filing object,
                'annual_type': '10-K' or '20-F',
                'quarterlies': List[Filing],
                'is_foreign': bool,
                'accounting_standard': 'US-GAAP' or 'IFRS'
            }
        """

        try:
            # Get company
            company = Company(ticker)

            # Get recent filings (last 2 years to ensure we get everything)
            filings = company.get_filings(
                form=["10-K", "10-Q", "20-F", "6-K"]
            ).to_pandas()

            if len(filings) == 0:
                raise ValueError(f"No filings found for {ticker}")

            # Find latest annual report (10-K or 20-F)
            annual_filing = None
            is_foreign = False

            for _, filing in filings.iterrows():
                if filing["form"] in ["10-K", "20-F"]:
                    annual_filing = filing
                    is_foreign = filing["form"] == "20-F"
                    break

            if annual_filing is None:
                raise ValueError(f"No annual report (10-K or 20-F) found for {ticker}")

            # Determine quarterly form type
            quarterly_form = "6-K" if is_foreign else "10-Q"
            accounting_standard = "IFRS" if is_foreign else "US-GAAP"

            # Get subsequent quarterly filings (max 3)
            annual_date = annual_filing["filing_date"]
            subsequent_quarterlies = []

            for _, filing in filings.iterrows():
                if (
                    filing["form"] == quarterly_form
                    and filing["filing_date"] > annual_date
                ):
                    subsequent_quarterlies.append(filing)
                    if len(subsequent_quarterlies) >= 3:
                        break

            logger.info(
                f"Found filings for {ticker}: {annual_filing['form']} + {len(subsequent_quarterlies)} quarterlies"
            )

            return {
                "annual": annual_filing,
                "annual_type": annual_filing["form"],
                "quarterlies": subsequent_quarterlies,
                "is_foreign": is_foreign,
                "accounting_standard": accounting_standard,
                "company": company,
            }

        except Exception as e:
            logger.error(f"Error getting filings for {ticker}: {e}")
            raise


# ========================================
# UTILITY FUNCTIONS
# ========================================


def get_filing_strategy(form_type: str, is_foreign: bool = False) -> Dict[str, Any]:
    """
    Determine filing strategy based on company type.

    Args:
        form_type: Filing form type (10-K, 20-F, etc.)
        is_foreign: Whether company is foreign issuer

    Returns:
        Dict with filing strategy details
    """
    if form_type == "20-F" or is_foreign:
        return {
            "annual_form": "20-F",
            "quarterly_form": "6-K",
            "is_foreign": True,
            "accounting_standard": "IFRS",
        }
    else:
        return {
            "annual_form": "10-K",
            "quarterly_form": "10-Q",
            "is_foreign": False,
            "accounting_standard": "US-GAAP",
        }
