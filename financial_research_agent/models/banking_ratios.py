"""
Pydantic models for banking-specific regulatory ratios.

These models capture Basel III capital ratios, liquidity metrics,
and other banking-specific financial metrics.
"""

from pydantic import BaseModel, Field
from typing import Optional


class BankingRegulatoryRatios(BaseModel):
    """
    Banking regulatory ratios and metrics.

    Combines directly reported ratios (from 10-K regulatory disclosures)
    with calculated banking-specific metrics.
    """

    # ==================== TIER 1: Directly Reported (Extracted from 10-K) ====================

    # Basel III Capital Ratios
    cet1_ratio: Optional[float] = Field(
        None,
        description="Common Equity Tier 1 Capital Ratio (%)"
    )
    tier1_ratio: Optional[float] = Field(
        None,
        description="Tier 1 Capital Ratio (%)"
    )
    total_capital_ratio: Optional[float] = Field(
        None,
        description="Total Capital Ratio (%)"
    )
    tier1_leverage_ratio: Optional[float] = Field(
        None,
        description="Tier 1 Leverage Ratio (%)"
    )
    supplementary_leverage_ratio: Optional[float] = Field(
        None,
        description="Supplementary Leverage Ratio (%) - G-SIBs only"
    )

    # Capital Components (in billions unless otherwise noted)
    cet1_capital: Optional[float] = Field(
        None,
        description="Common Equity Tier 1 Capital ($ billions)"
    )
    tier1_capital: Optional[float] = Field(
        None,
        description="Tier 1 Capital ($ billions)"
    )
    total_capital: Optional[float] = Field(
        None,
        description="Total Capital ($ billions)"
    )
    risk_weighted_assets: Optional[float] = Field(
        None,
        description="Risk-Weighted Assets ($ billions)"
    )

    # Liquidity Ratios
    lcr: Optional[float] = Field(
        None,
        description="Liquidity Coverage Ratio (%) - 30-day liquidity stress test"
    )
    nsfr: Optional[float] = Field(
        None,
        description="Net Stable Funding Ratio (%) - 1-year funding stability"
    )

    # U.S. Stress Test Requirements
    stress_capital_buffer: Optional[float] = Field(
        None,
        description="Stress Capital Buffer (%) - from annual stress test"
    )
    gsib_surcharge: Optional[float] = Field(
        None,
        description="G-SIB Surcharge (%) - 0% to 3.5% for largest banks"
    )

    # Regulatory Minimums (for context)
    cet1_minimum_required: Optional[float] = Field(
        None,
        description="Minimum CET1 ratio required (%) - typically 4.5% + buffers = 7%+"
    )
    tier1_minimum_required: Optional[float] = Field(
        None,
        description="Minimum Tier 1 ratio required (%) - typically 6% + buffers"
    )
    total_capital_minimum_required: Optional[float] = Field(
        None,
        description="Minimum Total Capital ratio required (%) - typically 8% + buffers"
    )

    # ==================== TIER 2: Calculated Ratios (from Financial Statements) ====================

    # Profitability Metrics
    net_interest_margin: Optional[float] = Field(
        None,
        description="Net Interest Margin (%) - core lending profitability"
    )
    efficiency_ratio: Optional[float] = Field(
        None,
        description="Efficiency Ratio (%) - lower is better (costs/revenue)"
    )
    return_on_tangible_equity: Optional[float] = Field(
        None,
        description="Return on Tangible Common Equity (%) - key profitability metric for banks"
    )

    # Credit Quality Metrics
    npl_ratio: Optional[float] = Field(
        None,
        description="Non-Performing Loan Ratio (%) - <1% is healthy"
    )
    provision_coverage_ratio: Optional[float] = Field(
        None,
        description="Provision Coverage Ratio (%) - reserves/NPLs, >80% is adequate"
    )
    net_charge_off_rate: Optional[float] = Field(
        None,
        description="Net Charge-Off Rate (%) - actual loan losses"
    )
    allowance_for_loan_losses: Optional[float] = Field(
        None,
        description="Allowance for Loan Losses as % of Total Loans"
    )

    # Balance Sheet Composition
    loan_to_deposit_ratio: Optional[float] = Field(
        None,
        description="Loan-to-Deposit Ratio (%) - <100% means excess deposits"
    )
    loan_to_assets_ratio: Optional[float] = Field(
        None,
        description="Loan-to-Assets Ratio (%) - concentration in lending"
    )
    deposits_to_assets_ratio: Optional[float] = Field(
        None,
        description="Deposits-to-Assets Ratio (%) - funding composition"
    )

    # ==================== Metadata ====================

    reporting_period: Optional[str] = Field(
        None,
        description="Reporting period (e.g., 'December 31, 2024' or 'Q4 2024')"
    )
    prior_period: Optional[str] = Field(
        None,
        description="Prior period for comparison (e.g., 'December 31, 2023')"
    )

    regulatory_framework: Optional[str] = Field(
        None,
        description="Regulatory framework (e.g., 'Basel III Standardized Approach')"
    )

    peer_group: Optional[str] = Field(
        None,
        description="Peer group classification (e.g., 'U.S. G-SIB', 'Large Regional')"
    )

    # ==================== Narrative Summaries ====================

    capital_assessment: Optional[str] = Field(
        None,
        description="Brief assessment of capital adequacy position"
    )

    credit_quality_assessment: Optional[str] = Field(
        None,
        description="Brief assessment of credit quality and loan portfolio health"
    )

    profitability_assessment: Optional[str] = Field(
        None,
        description="Brief assessment of profitability and efficiency"
    )

    key_strengths: Optional[list[str]] = Field(
        None,
        description="List of key strengths (e.g., 'Strong capital buffer', 'Low NPL ratio')"
    )

    key_concerns: Optional[list[str]] = Field(
        None,
        description="List of key concerns or areas to monitor"
    )

    def is_well_capitalized(self) -> bool:
        """Check if bank meets 'well-capitalized' regulatory standards."""
        if not self.cet1_ratio:
            return False

        # Well-capitalized thresholds (U.S. prompt corrective action)
        # CET1 >= 6.5%, Tier 1 >= 8%, Total >= 10%, Leverage >= 5%
        return self.cet1_ratio >= 6.5

    def capital_cushion(self) -> Optional[float]:
        """Calculate capital cushion above minimum requirement."""
        if not self.cet1_ratio or not self.cet1_minimum_required:
            return None

        return self.cet1_ratio - self.cet1_minimum_required

    def get_capital_status(self) -> str:
        """Get capital adequacy status description."""
        if not self.cet1_ratio:
            return "Unknown"

        if self.cet1_ratio >= 10.0:
            return "Well-Capitalized (Strong)"
        elif self.cet1_ratio >= 7.0:
            return "Well-Capitalized (Adequate)"
        elif self.cet1_ratio >= 4.5:
            return "Adequately Capitalized"
        else:
            return "Undercapitalized (Regulatory Concern)"

    def get_liquidity_status(self) -> str:
        """Get liquidity position status."""
        if not self.lcr:
            return "Unknown"

        if self.lcr >= 120:
            return "Strong Liquidity Position"
        elif self.lcr >= 100:
            return "Adequate Liquidity Position"
        else:
            return "Below Regulatory Minimum"

    def get_credit_quality_status(self) -> str:
        """Get credit quality status."""
        if not self.npl_ratio:
            return "Unknown"

        if self.npl_ratio < 1.0:
            return "Strong Credit Quality"
        elif self.npl_ratio < 2.0:
            return "Adequate Credit Quality"
        elif self.npl_ratio < 3.0:
            return "Moderate Credit Concerns"
        else:
            return "Significant Credit Quality Issues"
