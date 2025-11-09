"""
SEC Filing Checker - Detect new filings and compare against indexed data.

Uses edgartools library to check for the latest filings and determine if
indexed analyses are outdated.
"""
import os
from datetime import datetime
from typing import Optional


class SECFilingChecker:
    """Check SEC EDGAR for latest filings and compare to indexed data."""

    def __init__(self):
        """Initialize EDGAR client with proper user agent."""
        # Import here to avoid circular dependencies
        from edgar import set_identity

        # Get user agent from environment
        user_agent = os.getenv(
            "SEC_EDGAR_USER_AGENT",
            "FinancialResearchAgent/1.0 (your-email@example.com)"
        )

        # Set identity for edgartools
        set_identity(user_agent)

    def get_latest_filing_date(
        self,
        ticker: str,
        filing_types: list[str] = ["10-K", "10-Q"]
    ) -> Optional[dict]:
        """
        Get the date of the most recent filing for a ticker.

        Args:
            ticker: Stock ticker symbol
            filing_types: List of filing types to check (default: 10-K, 10-Q)

        Returns:
            {
                "ticker": str,
                "filing_type": str,  # "10-K" or "10-Q"
                "filing_date": str,  # "2024-11-01"
                "period_of_report": str,  # "2024-09-30"
                "accession_number": str
            }
            or None if no filings found
        """
        try:
            from edgar import Company

            # Get company filings
            company = Company(ticker)

            # Get recent filings of specified types
            for filing_type in filing_types:
                filings_result = company.get_filings(form=filing_type)

                if filings_result and len(filings_result) > 0:
                    filing = filings_result[0]  # Get latest filing
                    return {
                        "ticker": ticker.upper(),
                        "filing_type": filing_type,
                        "filing_date": str(filing.filing_date) if hasattr(filing, 'filing_date') else None,
                        "period_of_report": str(filing.period_of_report) if hasattr(filing, 'period_of_report') else None,
                        "accession_number": str(filing.accession_no) if hasattr(filing, 'accession_no') else None
                    }

            return None

        except Exception as e:
            print(f"Error fetching filings for {ticker}: {e}")
            return None

    def compare_to_indexed_date(
        self,
        ticker: str,
        indexed_date: str,
        filing_types: list[str] = ["10-K", "10-Q"]
    ) -> dict:
        """
        Compare indexed analysis date to latest SEC filing.

        Args:
            ticker: Stock ticker symbol
            indexed_date: Date of indexed analysis (YYYY-MM-DD or YYYYMMDD)
            filing_types: Filing types to check

        Returns:
            {
                "newer_filing_available": bool,
                "indexed_date": str,
                "latest_filing_date": str | None,
                "latest_filing_type": str | None,
                "days_behind": int | None,  # How many days behind
                "recommendation": str  # "refresh" | "ok" | "unknown"
            }
        """
        # Normalize indexed_date format
        if len(indexed_date) == 8 and indexed_date.isdigit():
            # Convert YYYYMMDD to YYYY-MM-DD
            indexed_date = f"{indexed_date[:4]}-{indexed_date[4:6]}-{indexed_date[6:8]}"

        indexed_dt = datetime.strptime(indexed_date, "%Y-%m-%d")

        # Get latest filing
        latest_filing = self.get_latest_filing_date(ticker, filing_types)

        if not latest_filing or not latest_filing.get("filing_date"):
            return {
                "newer_filing_available": False,
                "indexed_date": indexed_date,
                "latest_filing_date": None,
                "latest_filing_type": None,
                "days_behind": None,
                "recommendation": "unknown"
            }

        # Compare dates
        filing_dt = datetime.strptime(latest_filing["filing_date"], "%Y-%m-%d")
        days_behind = (filing_dt - indexed_dt).days

        newer_available = filing_dt > indexed_dt

        # Recommendation logic
        if not newer_available:
            recommendation = "ok"
        elif days_behind >= 30:
            recommendation = "refresh"  # Very outdated
        elif days_behind >= 7:
            recommendation = "refresh"  # Moderately outdated
        else:
            recommendation = "ok"  # Recent enough

        return {
            "newer_filing_available": newer_available,
            "indexed_date": indexed_date,
            "latest_filing_date": latest_filing["filing_date"],
            "latest_filing_type": latest_filing["filing_type"],
            "period_of_report": latest_filing.get("period_of_report"),
            "days_behind": days_behind if newer_available else 0,
            "recommendation": recommendation
        }

    def check_multiple_companies(
        self,
        companies: list[dict],
        filing_types: list[str] = ["10-K", "10-Q"]
    ) -> list[dict]:
        """
        Check multiple companies for filing updates.

        Args:
            companies: List of company dicts from chroma_manager.get_companies_with_status()
                       Each should have: ticker, last_updated
            filing_types: Filing types to check

        Returns:
            List of comparison results with update recommendations
        """
        results = []

        for company in companies:
            ticker = company["ticker"]
            indexed_date = company.get("last_updated", "")

            if not indexed_date or indexed_date == "Unknown":
                # Can't compare without a date
                results.append({
                    "ticker": ticker,
                    "newer_filing_available": False,
                    "recommendation": "unknown"
                })
                continue

            comparison = self.compare_to_indexed_date(
                ticker,
                indexed_date,
                filing_types
            )

            results.append({
                "ticker": ticker,
                "company": company.get("company", ""),
                **comparison
            })

        return results


def get_filing_checker() -> SECFilingChecker:
    """Get a SEC filing checker instance."""
    return SECFilingChecker()
