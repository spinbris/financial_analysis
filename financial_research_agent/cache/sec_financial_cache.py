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
        with open(schema_path, 'r') as f:
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
        cursor.execute("""
            SELECT 
                COUNT(*) as filing_count,
                MAX(filing_date) as latest_date,
                MAX(cached_at) as last_cached,
                MAX(is_foreign) as is_foreign
            FROM filings_metadata
            WHERE ticker = ?
        """, (ticker.upper(),))
        
        result = cursor.fetchone()
        filing_count = result['filing_count']
        latest_date = result['latest_date']
        last_cached = result['last_cached']
        is_foreign = bool(result['is_foreign']) if result['is_foreign'] is not None else False
        
        conn.close()
            
            # Not cached at all
        if filing_count == 0:
            return {
                'cached': False,
                'current': False,
                'needs_update': True,
                'cache_age_days': None,
                'filing_count': 0,
                'latest_filing_date': None,
                'is_foreign': False
            }
        
        # Calculate cache age
        cached_datetime = datetime.fromisoformat(last_cached)
        age_days = (datetime.now() - cached_datetime).days
        
        # Check if current (within max_age_days)
        is_current = age_days <= max_age_days
        
        return {
            'cached': True,
            'current': is_current,
            'needs_update': not is_current,
            'cache_age_days': age_days,
            'filing_count': filing_count,
            'latest_filing_date': latest_date,
            'is_foreign': is_foreign
        }
    
    def cache_filing(
        self, 
        ticker: str, 
        filing_data: Dict[str, Any]
    ) -> int:
        """
        Cache a single SEC filing.
        
        Args:
            ticker: Stock ticker symbol
            filing_data: Complete filing data from edgartools
            
        Returns:
            filing_id: Database ID of cached filing
        """
        # TODO: Implement tomorrow (Day 2)
        pass
    
    def get_cached_financials(
        self, 
        ticker: str, 
        periods: int = 4
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached financial data for a company.
        
        Args:
            ticker: Stock ticker symbol
            periods: Number of periods to retrieve
            
        Returns:
            Complete financial data or None if not cached
        """
        # TODO: Implement tomorrow (Day 2)
        pass
    
    def search_line_items(
        self, 
        ticker: str, 
        search_term: str,
        statement: str = 'all'
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
        # TODO: Implement Day 3
        pass
    
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
            'total_filings': total_filings,
            'unique_companies': unique_companies,
            'us_companies': domestic or 0,
            'foreign_companies': foreign or 0,
            'database_size_mb': round(db_size_mb, 2),
            'database_path': str(self.db_path)
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
            filings = company.get_filings(form=['10-K', '10-Q', '20-F', '6-K']).to_pandas()
            
            if len(filings) == 0:
                raise ValueError(f"No filings found for {ticker}")
            
            # Find latest annual report (10-K or 20-F)
            annual_filing = None
            is_foreign = False
            
            for _, filing in filings.iterrows():
                if filing['form'] in ['10-K', '20-F']:
                    annual_filing = filing
                    is_foreign = filing['form'] == '20-F'
                    break
            
            if annual_filing is None:
                raise ValueError(f"No annual report (10-K or 20-F) found for {ticker}")
            
            # Determine quarterly form type
            quarterly_form = '6-K' if is_foreign else '10-Q'
            accounting_standard = 'IFRS' if is_foreign else 'US-GAAP'
            
            # Get subsequent quarterly filings (max 3)
            annual_date = annual_filing['filing_date']
            subsequent_quarterlies = []
            
            for _, filing in filings.iterrows():
                if filing['form'] == quarterly_form and filing['filing_date'] > annual_date:
                    subsequent_quarterlies.append(filing)
                    if len(subsequent_quarterlies) >= 3:
                        break
            
            logger.info(f"Found filings for {ticker}: {annual_filing['form']} + {len(subsequent_quarterlies)} quarterlies")
            
            return {
                'annual': annual_filing,
                'annual_type': annual_filing['form'],
                'quarterlies': subsequent_quarterlies,
                'is_foreign': is_foreign,
                'accounting_standard': accounting_standard,
                'company': company
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
            'annual_form': '20-F',
            'quarterly_form': '6-K',
            'is_foreign': True,
            'accounting_standard': 'IFRS'
        }
    else:
        return {
            'annual_form': '10-K',
            'quarterly_form': '10-Q',
            'is_foreign': False,
            'accounting_standard': 'US-GAAP'
        }
        
