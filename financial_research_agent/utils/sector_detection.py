"""
Industry sector detection for specialized financial analysis.

Detects whether a company is a bank, insurance company, REIT, etc.
to enable sector-specific ratio analysis.
"""

from typing import Literal

IndustrySector = Literal['banking', 'investment_banking', 'insurance', 'reit', 'general']

# Curated lists of financial institutions
COMMERCIAL_BANKS = {
    # U.S. G-SIBs
    'JPM', 'BAC', 'C', 'WFC', 'BNY', 'STT',
    # Large U.S. Regional Banks
    'USB', 'PNC', 'TFC', 'COF', 'MTB', 'KEY', 'FITB', 'HBAN', 'RF', 'CFG',
    'FHN', 'CMA', 'ZION', 'WAL', 'WTFC', 'ONB', 'UBSI', 'CBSH', 'BOKF', 'ABCB',
    # Credit Card Banks (with bank charters)
    'AXP', 'DFS', 'SYF', 'COF',
    # International Banks (major ones that file with SEC)
    'HSBC',  # UK
    'RY', 'TD', 'BNS', 'BMO', 'CM',  # Canadian Big 5
    'BCS', 'DB', 'UBS', 'SAN', 'BBVA', 'ISP',  # European
    'MFG', 'SMFG', 'MUFG',  # Japanese
    'WBK', 'ITUB', 'BBD',  # Other international
}

INVESTMENT_BANKS = {
    'GS', 'MS',  # Bulge bracket (also have bank charters but focus on investment banking)
    'SCHW', 'IBKR', 'ETFC', 'AMTD',  # Brokerages
    'LAZ', 'EVR', 'PJT', 'MC', 'PIPR',  # Boutique investment banks
}

ASSET_MANAGERS = {
    'BLK', 'BX', 'KKR', 'APO', 'ARES', 'CG', 'BAM', 'ARCC',  # Private equity / alternatives
    'TROW', 'BEN', 'IVZ',  # Traditional asset managers
}

INSURANCE_COMPANIES = {
    'BRK.A', 'BRK.B', 'PGR', 'TRV', 'CB', 'AIG', 'MET', 'PRU', 'AFL', 'ALL',
    'HIG', 'CNA', 'WRB', 'RNR', 'L', 'LNC', 'UNM', 'TMK', 'RE', 'RGA',
}

REITS = {
    'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'DLR', 'O', 'WELL', 'AVB', 'EQR',
    'SPG', 'VTR', 'ARE', 'ESS', 'MAA', 'UDR', 'CPT', 'FRT', 'KIM', 'REG',
}

# SIC Code mappings for fallback detection
BANKING_SIC_CODES = {
    6020, 6021, 6022, 6029,  # Commercial banks
    6035, 6036,  # Savings institutions
}

INVESTMENT_SIC_CODES = {
    6211,  # Security brokers, dealers
    6282,  # Investment advice
}

INSURANCE_SIC_CODES = {
    6311, 6321, 6331, 6351, 6361, 6371, 6411,  # Various insurance types
}

REIT_SIC_CODES = {
    6798,  # Real Estate Investment Trusts
}


def detect_industry_sector(ticker: str, sic_code: int = None) -> IndustrySector:
    """
    Detect the industry sector for a given company.

    Args:
        ticker: Stock ticker symbol
        sic_code: Optional SIC code from SEC filings

    Returns:
        Industry sector classification
    """
    ticker = ticker.upper().strip()

    # Method 1: Ticker-based lookup (fastest, most reliable)
    if ticker in COMMERCIAL_BANKS:
        return 'banking'

    if ticker in INVESTMENT_BANKS or ticker in ASSET_MANAGERS:
        return 'investment_banking'

    if ticker in INSURANCE_COMPANIES:
        return 'insurance'

    if ticker in REITS:
        return 'reit'

    # Method 2: SIC code lookup (if provided)
    if sic_code:
        if sic_code in BANKING_SIC_CODES:
            return 'banking'

        if sic_code in INVESTMENT_SIC_CODES:
            return 'investment_banking'

        if sic_code in INSURANCE_SIC_CODES:
            return 'insurance'

        if sic_code in REIT_SIC_CODES:
            return 'reit'

    # Default: general company
    return 'general'


def should_analyze_banking_ratios(sector: IndustrySector) -> bool:
    """Check if banking ratios analysis should be run."""
    return sector == 'banking'


def should_analyze_investment_metrics(sector: IndustrySector) -> bool:
    """Check if investment banking metrics should be run."""
    return sector == 'investment_banking'


def get_peer_group(ticker: str, sector: IndustrySector) -> str:
    """
    Get peer group classification for benchmarking.

    Returns peer group name for comparison purposes.
    """
    ticker = ticker.upper()

    if sector == 'banking':
        # U.S. G-SIBs (systemically important)
        if ticker in {'JPM', 'BAC', 'C', 'WFC', 'GS', 'MS', 'BNY', 'STT'}:
            return 'U.S. G-SIB'

        # Large Regional Banks (>$100B assets)
        if ticker in {'USB', 'PNC', 'TFC', 'COF', 'MTB', 'KEY', 'FITB'}:
            return 'Large Regional Bank'

        # Mid-Size Regional Banks
        if ticker in {'HBAN', 'RF', 'CFG', 'FHN', 'CMA', 'ZION'}:
            return 'Regional Bank'

        # Canadian Big 5
        if ticker in {'RY', 'TD', 'BNS', 'BMO', 'CM'}:
            return 'Canadian Big 5'

        # European G-SIBs
        if ticker in {'HSBC', 'BCS', 'DB', 'UBS', 'SAN', 'BBVA'}:
            return 'European G-SIB'

        # Credit Card Banks
        if ticker in {'AXP', 'DFS', 'SYF'}:
            return 'Credit Card Bank'

        return 'Regional Bank'

    if sector == 'investment_banking':
        if ticker in {'GS', 'MS'}:
            return 'Bulge Bracket'

        if ticker in {'BLK', 'BX', 'KKR', 'APO', 'ARES'}:
            return 'Alternative Asset Manager'

        if ticker in {'SCHW', 'IBKR', 'ETFC'}:
            return 'Online Brokerage'

        return 'Investment Management'

    if sector == 'insurance':
        if ticker == 'BRK.A' or ticker == 'BRK.B':
            return 'Diversified Insurance'

        return 'Insurance'

    if sector == 'reit':
        return 'REIT'

    return 'General'


def get_sector_display_name(sector: IndustrySector) -> str:
    """Get human-readable sector name."""
    return {
        'banking': 'Commercial Banking',
        'investment_banking': 'Investment Banking & Asset Management',
        'insurance': 'Insurance',
        'reit': 'Real Estate Investment Trust (REIT)',
        'general': 'General'
    }.get(sector, 'General')
