"""
Tests for Financial Data Manager - Day 4
"""

import os
import pytest
from dataclasses import asdict

# Ensure EDGAR identity is set
os.environ.setdefault('EDGAR_IDENTITY', 'Test User test@example.com')


class TestRatioCalculator:
    """Test ratio calculations"""
    
    def test_profitability_ratios(self):
        from financial_data_manager import FinancialMetrics, RatioCalculator
        
        metrics = FinancialMetrics(
            ticker='TEST',
            company_name='Test Company',
            fiscal_year='FY 2025',
            source='test',
            revenue=1_000_000,
            net_income=100_000,
            gross_profit=400_000,
            operating_income=200_000,
            total_assets=2_000_000,
            shareholders_equity=500_000,
        )
        
        ratios = RatioCalculator.calculate_all(metrics)
        
        assert ratios.profit_margin == pytest.approx(0.10, rel=0.01)  # 10%
        assert ratios.operating_margin == pytest.approx(0.20, rel=0.01)  # 20%
        assert ratios.gross_margin == pytest.approx(0.40, rel=0.01)  # 40%
        assert ratios.roe == pytest.approx(0.20, rel=0.01)  # 20%
        assert ratios.roa == pytest.approx(0.05, rel=0.01)  # 5%
    
    def test_liquidity_ratios(self):
        from financial_data_manager import FinancialMetrics, RatioCalculator
        
        metrics = FinancialMetrics(
            ticker='TEST',
            company_name='Test Company',
            fiscal_year='FY 2025',
            source='test',
            current_assets=200_000,
            current_liabilities=100_000,
            cash=50_000,
        )
        
        ratios = RatioCalculator.calculate_all(metrics)
        
        assert ratios.current_ratio == pytest.approx(2.0, rel=0.01)
        assert ratios.cash_ratio == pytest.approx(0.5, rel=0.01)
    
    def test_leverage_ratios(self):
        from financial_data_manager import FinancialMetrics, RatioCalculator
        
        metrics = FinancialMetrics(
            ticker='TEST',
            company_name='Test Company',
            fiscal_year='FY 2025',
            source='test',
            total_assets=1_000_000,
            total_liabilities=600_000,
            shareholders_equity=400_000,
        )
        
        ratios = RatioCalculator.calculate_all(metrics)
        
        assert ratios.debt_to_equity == pytest.approx(1.5, rel=0.01)
        assert ratios.debt_to_assets == pytest.approx(0.6, rel=0.01)
        assert ratios.equity_multiplier == pytest.approx(2.5, rel=0.01)
    
    def test_handles_missing_data(self):
        from financial_data_manager import FinancialMetrics, RatioCalculator
        
        metrics = FinancialMetrics(
            ticker='TEST',
            company_name='Test Company',
            fiscal_year='FY 2025',
            source='test',
            revenue=None,
            net_income=None,
        )
        
        ratios = RatioCalculator.calculate_all(metrics)
        
        assert ratios.profit_margin is None
        assert ratios.roe is None
    
    def test_uses_precalculated_ratios(self):
        from financial_data_manager import FinancialMetrics, RatioCalculator
        
        metrics = FinancialMetrics(
            ticker='TEST',
            company_name='Test Company',
            fiscal_year='FY 2025',
            source='edgartools',
            revenue=1_000_000,
            net_income=100_000,
            profit_margin=0.12,  # Pre-calculated (different from 0.10)
            operating_margin=0.25,
        )
        
        ratios = RatioCalculator.calculate_all(metrics)
        
        # Should use pre-calculated values
        assert ratios.profit_margin == pytest.approx(0.12, rel=0.01)
        assert ratios.operating_margin == pytest.approx(0.25, rel=0.01)


class TestFinancialDataManager:
    """Test the unified data manager"""
    
    @pytest.mark.integration
    def test_get_metrics_usgaap(self):
        """Test fetching US-GAAP company (requires network)"""
        from financial_data_manager import FinancialDataManager
        
        manager = FinancialDataManager()
        metrics = manager.get_metrics('AAPL', periods=1)
        
        assert len(metrics) >= 1
        m = metrics[0]
        
        assert m.ticker == 'AAPL'
        assert m.source in ['edgartools', 'xbrl_cache', 'edgartools+xbrl_cache']
        assert m.revenue is not None
        assert m.revenue > 100_000_000_000  # > $100B
    
    @pytest.mark.integration
    def test_get_ratios(self):
        """Test ratio calculation (requires network)"""
        from financial_data_manager import FinancialDataManager
        
        manager = FinancialDataManager()
        ratios = manager.get_ratios('AAPL', periods=1)
        
        assert len(ratios) >= 1
        r = ratios[0]
        
        assert r.profit_margin is not None
        assert 0.1 < r.profit_margin < 0.5  # 10-50% margin
    
    @pytest.mark.integration
    def test_compare_companies(self):
        """Test company comparison (requires network)"""
        from financial_data_manager import compare_companies
        
        comparison = compare_companies(['AAPL', 'MSFT'])
        
        assert 'AAPL' in comparison
        assert 'MSFT' in comparison
        
        assert comparison['AAPL']['metrics']['revenue'] is not None
        assert comparison['MSFT']['metrics']['revenue'] is not None


class TestEdgartoolsIntegration:
    """Test edgartools-specific functionality"""
    
    @pytest.mark.integration
    def test_to_llm_context_structure(self):
        """Test edgartools to_llm_context output structure"""
        from edgar import Company
        
        company = Company('AAPL')
        stmt = company.income_statement(periods=2)
        ctx = stmt.to_llm_context()
        
        assert 'data' in ctx
        assert 'key_metrics' in ctx
        assert 'periods' in ctx
        
        # Check key_metrics has ratios
        km = ctx.get('key_metrics', {})
        assert any('profit_margin' in k for k in km.keys())
    
    @pytest.mark.integration
    def test_balance_sheet_find_item(self):
        """Test find_item on balance sheet"""
        from edgar import Company
        
        company = Company('AAPL')
        bs = company.balance_sheet(periods=2)
        
        assets = bs.find_item('Assets')
        assert assets is not None
        assert assets.values is not None
        assert len(assets.values) > 0


if __name__ == '__main__':
    # Run unit tests only (no network required)
    pytest.main([__file__, '-v', '-m', 'not integration'])
