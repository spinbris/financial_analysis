"""
Cached Financial Manager - Integration layer using XBRL concepts.
"""

import time
from typing import Dict, List, Optional, Any, Union
import logging

from .sec_financial_cache import SecFinancialCache

logger = logging.getLogger(__name__)


class CachedFinancialManager:
    """
    High-level manager for cached financial data.
    Uses standardized XBRL concepts for cross-standard compatibility.
    """
    
    def __init__(self, db_path: str = "data/sec_cache/financials.db"):
        """Initialize the manager."""
        self.cache = SecFinancialCache(db_path)
        self._concept_map = self._build_concept_map()
    
    def _build_concept_map(self) -> Dict[str, List[str]]:
        """
        Map friendly metric names to XBRL concepts.
        Lists concepts in priority order: [US-GAAP, IFRS, ...]
        """
        return {
            # Balance Sheet
            'assets': ['us-gaap_Assets', 'ifrs-full_Assets'],
            'current_assets': ['us-gaap_AssetsCurrent', 'ifrs-full_CurrentAssets'],
            'noncurrent_assets': ['us-gaap_AssetsNoncurrent', 'ifrs-full_NoncurrentAssets'],
            'liabilities': ['us-gaap_Liabilities', 'ifrs-full_Liabilities'],
            'current_liabilities': ['us-gaap_LiabilitiesCurrent', 'ifrs-full_CurrentLiabilities'],
            'noncurrent_liabilities': ['us-gaap_LiabilitiesNoncurrent', 'ifrs-full_NoncurrentLiabilities'],
            'equity': ['us-gaap_StockholdersEquity', 'ifrs-full_Equity', 'ifrs-full_EquityAttributableToOwnersOfParent'],
            'cash': ['us-gaap_CashAndCashEquivalentsAtCarryingValue', 'ifrs-full_CashAndCashEquivalents'],
            'inventory': ['us-gaap_InventoryNet', 'ifrs-full_Inventories'],
            'receivables': ['us-gaap_AccountsReceivableNetCurrent', 'ifrs-full_TradeAndOtherCurrentReceivables'],
            'payables': ['us-gaap_AccountsPayableCurrent', 'ifrs-full_TradeAndOtherCurrentPayables'],
            'ppe': ['us-gaap_PropertyPlantAndEquipmentNet', 'ifrs-full_PropertyPlantAndEquipment'],
            'retained_earnings': ['us-gaap_RetainedEarningsAccumulatedDeficit', 'ifrs-full_RetainedEarnings'],
            'long_term_debt': ['us-gaap_LongTermDebtNoncurrent', 'bhp_NonCurrentInterestBearingLiabilities'],
            
            # Income Statement (need to check these)
            'revenue': ['us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax', 'us-gaap_Revenues', 'ifrs-full_Revenue'],
            'net_income': ['us-gaap_NetIncomeLoss', 'ifrs-full_ProfitLoss'],
            'operating_income': ['us-gaap_OperatingIncomeLoss', 'ifrs-full_ProfitLossFromOperatingActivities'],
            'gross_profit': ['us-gaap_GrossProfit', 'ifrs-full_GrossProfit'],
            'cost_of_revenue': ['us-gaap_CostOfGoodsAndServicesSold', 'ifrs-full_CostOfSales'],
            
            # Cash Flow
            'operating_cash_flow': ['us-gaap_NetCashProvidedByUsedInOperatingActivities', 'ifrs-full_CashFlowsFromUsedInOperatingActivities'],
            'investing_cash_flow': ['us-gaap_NetCashProvidedByUsedInInvestingActivities', 'ifrs-full_CashFlowsFromUsedInInvestingActivities'],
            'financing_cash_flow': ['us-gaap_NetCashProvidedByUsedInFinancingActivities', 'ifrs-full_CashFlowsFromUsedInFinancingActivities'],
        }
    
    def _get_by_concept(self, ticker: str, concepts: List[str]) -> Optional[float]:
        """Get value by trying each concept in order."""
        conn = self.cache._get_connection()
        cursor = conn.cursor()
        
        for concept in concepts:
            for table in ['balance_sheet', 'income_statement', 'cash_flow']:
                cursor.execute(f"""
                    SELECT value FROM {table}
                    WHERE ticker = ? AND concept = ?
                    ORDER BY filing_date DESC
                    LIMIT 1
                """, (ticker.upper(), concept))
                
                row = cursor.fetchone()
                if row and row['value'] is not None:
                    conn.close()
                    return row['value']
        
        conn.close()
        return None
    
    def get_financials(
        self,
        ticker: str,
        force_refresh: bool = False,
        periods: int = 4
    ) -> Dict[str, Any]:
        """Get financial data for a company (cache-first)."""
        start_time = time.time()
        
        status = self.cache.check_cache_status(ticker)
        
        if not status['cached'] or not status['current'] or force_refresh:
            logger.info(f"Cache miss for {ticker}, fetching from SEC...")
            cache_result = self.cache.cache_company(ticker, force_refresh=force_refresh)
            
            if cache_result.get('error'):
                return {
                    'ticker': ticker,
                    'error': cache_result['error'],
                    'source': 'error'
                }
            source = 'sec'
        else:
            source = 'cache'
        
        data = self.cache.get_cached_financials(ticker, periods=periods)
        elapsed = time.time() - start_time
        
        return {
            'ticker': ticker,
            'source': source,
            'retrieval_time_ms': round(elapsed * 1000, 2),
            'cache_age_days': status.get('cache_age_days'),
            'is_foreign': status.get('is_foreign', False),
            'periods': data.get('periods', []) if data else []
        }
    
    def get_metric(self, ticker: str, metric: str) -> Optional[float]:
        """Get a specific metric for a company using XBRL concepts."""
        self.get_financials(ticker)
        
        concepts = self._concept_map.get(metric.lower())
        if concepts:
            return self._get_by_concept(ticker, concepts)
        
        # Fallback: search by label
        results = self.cache.search_line_items(metric, ticker=ticker, limit=1)
        return results[0]['value'] if results else None
    
    def compare(
        self,
        tickers: List[str],
        metrics: List[str]
    ) -> Dict[str, Dict[str, Optional[float]]]:
        """Compare metrics across multiple companies."""
        for ticker in tickers:
            self.get_financials(ticker)
        
        result = {}
        for ticker in tickers:
            result[ticker] = {}
            for metric in metrics:
                result[ticker][metric] = self.get_metric(ticker, metric)
        
        return result
    
    def search(self, search_term: str, ticker: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for financial items by label or concept."""
        if ticker:
            self.get_financials(ticker)
        return self.cache.search_line_items(search_term, ticker=ticker, limit=limit)
    
    def get_key_metrics(self, ticker: str) -> Dict[str, Optional[float]]:
        """Get key financial metrics for a company."""
        self.get_financials(ticker)
        
        key_metrics = ['assets', 'liabilities', 'equity', 'cash', 'revenue', 'net_income']
        
        return {metric: self.get_metric(ticker, metric) for metric in key_metrics}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.get_cache_stats()
    
    def close(self):
        """Close the cache connection."""
        self.cache.close()
