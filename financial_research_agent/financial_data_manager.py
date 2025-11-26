"""
Unified Financial Data Manager
EdgarTools-first with XBRL cache fallback for IFRS companies

Day 4 Implementation - SEC Cache Foundation
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Optional, Any, List, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

# Set EDGAR identity before importing edgar
if not os.environ.get('EDGAR_IDENTITY'):
    os.environ['EDGAR_IDENTITY'] = os.environ.get(
        'SEC_EDGAR_USER_AGENT', 
        'FinancialResearchAgent/1.0 (contact@example.com)'
    )

from edgar import Company


@dataclass
class FinancialMetrics:
    """Standardized financial metrics from any source"""
    ticker: str
    company_name: str
    fiscal_year: str
    source: str  # 'edgartools' or 'xbrl_cache'
    
    # Core metrics
    revenue: Optional[float] = None
    net_income: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    
    # Balance sheet
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    shareholders_equity: Optional[float] = None
    current_assets: Optional[float] = None
    current_liabilities: Optional[float] = None
    cash: Optional[float] = None
    
    # Cash flow
    operating_cash_flow: Optional[float] = None
    capital_expenditures: Optional[float] = None
    free_cash_flow: Optional[float] = None
    
    # Pre-calculated ratios (from edgartools when available)
    profit_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    revenue_growth: Optional[float] = None
    
    # Metadata
    retrieved_at: str = None
    
    def __post_init__(self):
        if self.retrieved_at is None:
            self.retrieved_at = datetime.utcnow().isoformat()


@dataclass 
class CalculatedRatios:
    """Cross-statement financial ratios"""
    ticker: str
    fiscal_year: str
    
    # Profitability
    profit_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    gross_margin: Optional[float] = None
    roe: Optional[float] = None  # Return on Equity
    roa: Optional[float] = None  # Return on Assets
    
    # Liquidity
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    cash_ratio: Optional[float] = None
    
    # Leverage
    debt_to_equity: Optional[float] = None
    debt_to_assets: Optional[float] = None
    equity_multiplier: Optional[float] = None
    
    # Efficiency
    asset_turnover: Optional[float] = None
    
    # Cash flow
    operating_cash_flow_ratio: Optional[float] = None
    free_cash_flow_margin: Optional[float] = None
    
    calculated_at: str = None
    
    def __post_init__(self):
        if self.calculated_at is None:
            self.calculated_at = datetime.utcnow().isoformat()


class RatioCalculator:
    """Calculate financial ratios from metrics"""
    
    @staticmethod
    def calculate_all(metrics: FinancialMetrics) -> CalculatedRatios:
        """Calculate all available ratios from financial metrics"""
        ratios = CalculatedRatios(
            ticker=metrics.ticker,
            fiscal_year=metrics.fiscal_year
        )
        
        # Profitability ratios
        if metrics.revenue and metrics.revenue > 0:
            if metrics.net_income is not None:
                ratios.profit_margin = metrics.net_income / metrics.revenue
            if metrics.operating_income is not None:
                ratios.operating_margin = metrics.operating_income / metrics.revenue
            if metrics.gross_profit is not None:
                ratios.gross_margin = metrics.gross_profit / metrics.revenue
        
        # ROE and ROA
        if metrics.net_income is not None:
            if metrics.shareholders_equity and metrics.shareholders_equity > 0:
                ratios.roe = metrics.net_income / metrics.shareholders_equity
            if metrics.total_assets and metrics.total_assets > 0:
                ratios.roa = metrics.net_income / metrics.total_assets
        
        # Liquidity ratios
        if metrics.current_liabilities and metrics.current_liabilities > 0:
            if metrics.current_assets is not None:
                ratios.current_ratio = metrics.current_assets / metrics.current_liabilities
            if metrics.cash is not None:
                ratios.cash_ratio = metrics.cash / metrics.current_liabilities
            # Quick ratio = (current assets - inventory) / current liabilities
            # We don't have inventory separately, so approximate with cash + receivables
            if metrics.current_assets and metrics.cash:
                # Rough approximation: quick assets ≈ 70% of current assets for tech
                ratios.quick_ratio = (metrics.current_assets * 0.7) / metrics.current_liabilities
        
        # Leverage ratios
        if metrics.shareholders_equity and metrics.shareholders_equity > 0:
            if metrics.total_liabilities is not None:
                ratios.debt_to_equity = metrics.total_liabilities / metrics.shareholders_equity
            if metrics.total_assets is not None:
                ratios.equity_multiplier = metrics.total_assets / metrics.shareholders_equity
        
        if metrics.total_assets and metrics.total_assets > 0:
            if metrics.total_liabilities is not None:
                ratios.debt_to_assets = metrics.total_liabilities / metrics.total_assets
            if metrics.revenue is not None:
                ratios.asset_turnover = metrics.revenue / metrics.total_assets
        
        # Cash flow ratios
        if metrics.operating_cash_flow is not None:
            if metrics.current_liabilities and metrics.current_liabilities > 0:
                ratios.operating_cash_flow_ratio = metrics.operating_cash_flow / metrics.current_liabilities
            if metrics.revenue and metrics.revenue > 0:
                ratios.free_cash_flow_margin = (
                    (metrics.operating_cash_flow - (metrics.capital_expenditures or 0)) 
                    / metrics.revenue
                )
        
        # Use pre-calculated values from edgartools if available
        if metrics.profit_margin is not None:
            ratios.profit_margin = metrics.profit_margin
        if metrics.operating_margin is not None:
            ratios.operating_margin = metrics.operating_margin
        
        return ratios


class FinancialDataManager:
    """
    Unified financial data manager with dual-source strategy:
    1. EdgarTools high-level API (primary) - great for US-GAAP
    2. XBRL concept cache (fallback) - required for IFRS companies
    """
    
    # XBRL concept mappings for fallback (from Day 3)
    CONCEPT_MAP = {
        'revenue': [
            'us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax',
            'us-gaap_Revenues',
            'ifrs-full_Revenue'
        ],
        'net_income': [
            'us-gaap_NetIncomeLoss',
            'ifrs-full_ProfitLoss'
        ],
        'gross_profit': [
            'us-gaap_GrossProfit',
            'ifrs-full_GrossProfit'
        ],
        'operating_income': [
            'us-gaap_OperatingIncomeLoss',
            'ifrs-full_ProfitLossFromOperatingActivities'
        ],
        'total_assets': [
            'us-gaap_Assets',
            'ifrs-full_Assets'
        ],
        'total_liabilities': [
            'us-gaap_Liabilities',
            'ifrs-full_Liabilities'
        ],
        'shareholders_equity': [
            'us-gaap_StockholdersEquity',
            'us-gaap_StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest',
            'ifrs-full_Equity',
            'ifrs-full_EquityAttributableToOwnersOfParent'
        ],
        'current_assets': [
            'us-gaap_AssetsCurrent',
            'ifrs-full_CurrentAssets'
        ],
        'current_liabilities': [
            'us-gaap_LiabilitiesCurrent',
            'ifrs-full_CurrentLiabilities'
        ],
        'cash': [
            'us-gaap_CashAndCashEquivalentsAtCarryingValue',
            'ifrs-full_CashAndCashEquivalents'
        ],
        'operating_cash_flow': [
            'us-gaap_NetCashProvidedByUsedInOperatingActivities',
            'ifrs-full_CashFlowsFromUsedInOperatingActivities'
        ],
        'capital_expenditures': [
            'us-gaap_PaymentsToAcquirePropertyPlantAndEquipment',
            'ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities'
        ],
    }
    
    def __init__(self, cache_db_path: Optional[str] = None):
        """
        Initialize the manager with optional cache database path.
        
        Args:
            cache_db_path: Path to SQLite cache database. If None, uses default location.
        """
        self.cache_db_path = cache_db_path or self._default_cache_path()
        self._ensure_cache_tables()
    
    def _default_cache_path(self) -> str:
        """Get default cache database path"""
        # Use existing project database
        project_root = Path(__file__).parent.parent
        return str(project_root / 'data' / 'sec_cache' / 'financials.db')
    
    def _ensure_cache_tables(self):
        """Ensure cache tables exist"""
        with sqlite3.connect(self.cache_db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS metrics_cache (
                    ticker TEXT,
                    fiscal_year TEXT,
                    data JSON,
                    source TEXT,
                    cached_at TEXT,
                    PRIMARY KEY (ticker, fiscal_year)
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ratios_cache (
                    ticker TEXT,
                    fiscal_year TEXT,
                    data JSON,
                    cached_at TEXT,
                    PRIMARY KEY (ticker, fiscal_year)
                )
            ''')
            conn.commit()
    
    def get_metrics(
        self, 
        ticker: str, 
        periods: int = 1,
        use_cache: bool = True,
        force_refresh: bool = False
    ) -> List[FinancialMetrics]:
        """
        Get financial metrics for a company.
        
        Args:
            ticker: Company ticker symbol
            periods: Number of fiscal periods to retrieve
            use_cache: Whether to use cached data
            force_refresh: Force refresh from source even if cached
            
        Returns:
            List of FinancialMetrics for each period
        """
        results = []
        
        for period_idx in range(periods):
            # Try cache first
            if use_cache and not force_refresh:
                cached = self._get_cached_metrics(ticker, period_idx)
                if cached:
                    results.append(cached)
                    continue
            
            # Fetch from source
            metrics = self._fetch_metrics(ticker, periods)
            if metrics:
                for m in metrics:
                    self._cache_metrics(m)
                results.extend(metrics)
                break  # Already got all periods
        
        return results[:periods]
    
    def _fetch_metrics(self, ticker: str, periods: int) -> List[FinancialMetrics]:
        """Fetch metrics using edgartools-first strategy with XBRL fallback"""
        
        # Try EdgarTools first
        metrics = self._try_edgartools(ticker, periods)
        
        if metrics and self._is_complete(metrics[0]):
            return metrics
        
        # Fallback to XBRL cache for missing data
        xbrl_metrics = self._try_xbrl_cache(ticker, periods)
        
        if xbrl_metrics:
            # Merge: prefer edgartools, fill gaps with XBRL
            if metrics:
                return self._merge_metrics(metrics, xbrl_metrics)
            return xbrl_metrics
        
        return metrics or []
    
    def _try_edgartools(self, ticker: str, periods: int) -> Optional[List[FinancialMetrics]]:
        """Try to get data from EdgarTools high-level API"""
        try:
            company = Company(ticker)
            
            # Get all three statements
            income = company.income_statement(periods=periods)
            balance = company.balance_sheet(periods=periods)
            cash_flow = company.cash_flow(periods=periods)
            
            # Get LLM context (includes pre-calculated metrics)
            income_ctx = income.to_llm_context() if income else {}
            balance_ctx = balance.to_llm_context() if balance else {}
            cash_ctx = cash_flow.to_llm_context() if cash_flow else {}
            
            # Extract periods
            stmt_periods = income_ctx.get('periods', []) or balance_ctx.get('periods', [])
            
            results = []
            for period in stmt_periods:
                period_key = period.lower().replace(' ', '_')
                
                metrics = FinancialMetrics(
                    ticker=ticker.upper(),
                    company_name=company.name,
                    fiscal_year=period,
                    source='edgartools',
                    
                    # Income statement
                    revenue=self._extract_value(income_ctx, ['total_revenue', 'revenuefromcontractwithcustomerexcludingassessedtax'], period_key),
                    net_income=self._extract_value(income_ctx, ['netincomeloss', 'net_income_loss_attributable_to_parent'], period_key),
                    gross_profit=self._extract_value(income_ctx, ['grossprofit', 'gross_profit'], period_key),
                    operating_income=self._extract_value(income_ctx, ['operatingincomeloss', 'operating_income_loss'], period_key),
                    
                    # Balance sheet
                    total_assets=self._extract_value(balance_ctx, ['assets', 'total_assets'], period_key),
                    total_liabilities=self._extract_value(balance_ctx, ['liabilities', 'total_liabilities'], period_key),
                    shareholders_equity=self._extract_value(balance_ctx, ['stockholdersequity', 'equity'], period_key),
                    current_assets=self._extract_value(balance_ctx, ['assetscurrent', 'assets_current'], period_key),
                    current_liabilities=self._extract_value(balance_ctx, ['liabilitiescurrent', 'liabilities_current'], period_key),
                    cash=self._extract_value(balance_ctx, ['cashandcashequivalentsatcarryingvalue', 'cash_and_cash_equivalents'], period_key),
                    
                    # Cash flow
                    operating_cash_flow=self._extract_value(cash_ctx, ['netcashprovidedbyusedinoperatingactivities'], period_key),
                    capital_expenditures=self._extract_value(cash_ctx, ['paymentstoacquirepropertyplantandequipment'], period_key),
                    
                    # Pre-calculated ratios from edgartools
                    profit_margin=income_ctx.get('key_metrics', {}).get(f'profit_margin_{period_key}'),
                    operating_margin=income_ctx.get('key_metrics', {}).get(f'operating_margin_{period_key}'),
                    revenue_growth=income_ctx.get('key_metrics', {}).get('revenue_growth_rate'),
                )
                
                results.append(metrics)
            
            return results if results else None
            
        except Exception as e:
            print(f"EdgarTools error for {ticker}: {e}")
            return None
    
    def _extract_value(self, ctx: dict, keys: List[str], period_key: str) -> Optional[float]:
        """Extract value from to_llm_context data dict"""
        data = ctx.get('data', {})
        for key in keys:
            # Try with period suffix
            value = data.get(f'{key}_{period_key}')
            if value is not None:
                return float(value)
        return None
    
    def _try_xbrl_cache(self, ticker: str, periods: int) -> Optional[List[FinancialMetrics]]:
        """Try to get data from our XBRL concept cache (Day 3 implementation)"""
        try:
            # Import the cached manager from Day 3
            from financial_research_agent.cache.cached_manager import CachedFinancialManager
            
            manager = CachedFinancialManager()
            
            # Get metrics using concept-based lookup
            results = []
            
            # For now, get latest period only from cache
            metrics = FinancialMetrics(
                ticker=ticker.upper(),
                company_name=ticker.upper(),  # Cache doesn't store company name
                fiscal_year='Latest',
                source='xbrl_cache',
                
                revenue=manager.get_metric(ticker, 'revenue'),
                net_income=manager.get_metric(ticker, 'net_income'),
                gross_profit=manager.get_metric(ticker, 'gross_profit'),
                operating_income=manager.get_metric(ticker, 'operating_income'),
                total_assets=manager.get_metric(ticker, 'assets'),
                total_liabilities=manager.get_metric(ticker, 'liabilities'),
                shareholders_equity=manager.get_metric(ticker, 'equity'),
                current_assets=manager.get_metric(ticker, 'current_assets'),
                current_liabilities=manager.get_metric(ticker, 'current_liabilities'),
                cash=manager.get_metric(ticker, 'cash'),
                operating_cash_flow=manager.get_metric(ticker, 'operating_cash_flow'),
            )
            
            if self._has_any_data(metrics):
                results.append(metrics)
            
            return results if results else None
            
        except ImportError:
            print("XBRL cache not available")
            return None
        except Exception as e:
            print(f"XBRL cache error for {ticker}: {e}")
            return None
    
    def _is_complete(self, metrics: FinancialMetrics) -> bool:
        """Check if metrics has essential data"""
        return all([
            metrics.revenue is not None,
            metrics.net_income is not None,
            metrics.total_assets is not None,
            metrics.shareholders_equity is not None,
        ])
    
    def _has_any_data(self, metrics: FinancialMetrics) -> bool:
        """Check if metrics has any data at all"""
        return any([
            metrics.revenue is not None,
            metrics.net_income is not None,
            metrics.total_assets is not None,
        ])
    
    def _merge_metrics(
        self, 
        primary: List[FinancialMetrics], 
        fallback: List[FinancialMetrics]
    ) -> List[FinancialMetrics]:
        """Merge metrics, preferring primary and filling gaps from fallback"""
        if not fallback:
            return primary
        
        merged = []
        fb = fallback[0] if fallback else None
        
        for m in primary:
            if fb:
                # Fill gaps
                if m.revenue is None:
                    m.revenue = fb.revenue
                if m.net_income is None:
                    m.net_income = fb.net_income
                if m.shareholders_equity is None:
                    m.shareholders_equity = fb.shareholders_equity
                if m.total_assets is None:
                    m.total_assets = fb.total_assets
                if m.total_liabilities is None:
                    m.total_liabilities = fb.total_liabilities
                if m.current_assets is None:
                    m.current_assets = fb.current_assets
                if m.current_liabilities is None:
                    m.current_liabilities = fb.current_liabilities
                if m.cash is None:
                    m.cash = fb.cash
                
                m.source = 'edgartools+xbrl_cache'
            
            merged.append(m)
        
        return merged
    
    def _get_cached_metrics(self, ticker: str, period_idx: int) -> Optional[FinancialMetrics]:
        """Get cached metrics"""
        # For now, simple implementation
        return None
    
    def _cache_metrics(self, metrics: FinancialMetrics):
        """Cache metrics to database"""
        with sqlite3.connect(self.cache_db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO metrics_cache (ticker, fiscal_year, data, source, cached_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                metrics.ticker,
                metrics.fiscal_year,
                json.dumps(asdict(metrics)),
                metrics.source,
                datetime.utcnow().isoformat()
            ))
            conn.commit()
    
    def get_ratios(self, ticker: str, periods: int = 1) -> List[CalculatedRatios]:
        """Get calculated ratios for a company"""
        metrics_list = self.get_metrics(ticker, periods)
        return [RatioCalculator.calculate_all(m) for m in metrics_list]
    
    def compare(
        self, 
        tickers: List[str], 
        metrics: Optional[List[str]] = None
    ) -> Dict[str, FinancialMetrics]:
        """Compare multiple companies"""
        results = {}
        for ticker in tickers:
            data = self.get_metrics(ticker, periods=1)
            if data:
                results[ticker] = data[0]
        return results
    
    def compare_ratios(
        self, 
        tickers: List[str]
    ) -> Dict[str, CalculatedRatios]:
        """Compare ratios across multiple companies"""
        results = {}
        for ticker in tickers:
            ratios = self.get_ratios(ticker, periods=1)
            if ratios:
                results[ticker] = ratios[0]
        return results


# Convenience functions
def get_financial_metrics(ticker: str, periods: int = 1) -> List[FinancialMetrics]:
    """Quick access to financial metrics"""
    manager = FinancialDataManager()
    return manager.get_metrics(ticker, periods)


def get_financial_ratios(ticker: str, periods: int = 1) -> List[CalculatedRatios]:
    """Quick access to financial ratios"""
    manager = FinancialDataManager()
    return manager.get_ratios(ticker, periods)


def compare_companies(tickers: List[str]) -> Dict[str, Dict]:
    """Compare multiple companies with metrics and ratios"""
    manager = FinancialDataManager()
    
    results = {}
    for ticker in tickers:
        metrics = manager.get_metrics(ticker, periods=1)
        if metrics:
            ratios = RatioCalculator.calculate_all(metrics[0])
            results[ticker] = {
                'metrics': asdict(metrics[0]),
                'ratios': asdict(ratios)
            }
    
    return results


if __name__ == '__main__':
    # Test the manager
    print("=" * 60)
    print("Financial Data Manager - Day 4 Test")
    print("=" * 60)
    
    manager = FinancialDataManager()
    
    # Test US-GAAP company (should use edgartools)
    print("\n=== AAPL (US-GAAP) ===")
    aapl_metrics = manager.get_metrics('AAPL', periods=2)
    for m in aapl_metrics:
        print(f"\n{m.fiscal_year} (source: {m.source}):")
        print(f"  Revenue: ${m.revenue:,.0f}" if m.revenue else "  Revenue: N/A")
        print(f"  Net Income: ${m.net_income:,.0f}" if m.net_income else "  Net Income: N/A")
        print(f"  Equity: ${m.shareholders_equity:,.0f}" if m.shareholders_equity else "  Equity: N/A")
    
    # Calculate ratios
    aapl_ratios = manager.get_ratios('AAPL', periods=1)
    if aapl_ratios:
        r = aapl_ratios[0]
        print(f"\nRatios:")
        print(f"  Profit Margin: {r.profit_margin:.2%}" if r.profit_margin else "  Profit Margin: N/A")
        print(f"  ROE: {r.roe:.2%}" if r.roe else "  ROE: N/A")
        print(f"  ROA: {r.roa:.2%}" if r.roa else "  ROA: N/A")
        print(f"  Current Ratio: {r.current_ratio:.2f}" if r.current_ratio else "  Current Ratio: N/A")
    
    # Test IFRS company (may need XBRL fallback)
    print("\n=== BHP (IFRS) ===")
    bhp_metrics = manager.get_metrics('BHP', periods=1)
    for m in bhp_metrics:
        print(f"\n{m.fiscal_year} (source: {m.source}):")
        print(f"  Revenue: ${m.revenue:,.0f}" if m.revenue else "  Revenue: N/A")
        print(f"  Net Income: ${m.net_income:,.0f}" if m.net_income else "  Net Income: N/A")
        print(f"  Equity: ${m.shareholders_equity:,.0f}" if m.shareholders_equity else "  Equity: N/A")
    
    # Compare companies
    print("\n=== Company Comparison ===")
    comparison = compare_companies(['AAPL', 'MSFT'])
    for ticker, data in comparison.items():
        print(f"\n{ticker}:")
        print(f"  Revenue: ${data['metrics']['revenue']:,.0f}" if data['metrics']['revenue'] else "  Revenue: N/A")
        print(f"  ROE: {data['ratios']['roe']:.2%}" if data['ratios']['roe'] else "  ROE: N/A")
