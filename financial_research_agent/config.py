"""Configuration for the financial research agent."""

import os
from pathlib import Path


class AgentConfig:
    """Configuration for agent models and settings."""

    # Model configurations
    PLANNER_MODEL = os.getenv("PLANNER_MODEL", "o3-mini")
    SEARCH_MODEL = os.getenv("SEARCH_MODEL", "gpt-4.1")
    WRITER_MODEL = os.getenv("WRITER_MODEL", "gpt-4.1")
    VERIFIER_MODEL = os.getenv("VERIFIER_MODEL", "gpt-4o")
    EDGAR_MODEL = os.getenv("EDGAR_MODEL", "gpt-4.1")

    # Search configuration
    MAX_SEARCH_RETRIES = int(os.getenv("MAX_SEARCH_RETRIES", "3"))
    SEARCH_RETRY_DELAY = float(os.getenv("SEARCH_RETRY_DELAY", "2.0"))

    # Output configuration
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "financial_research_agent/output")

    # Feature flags
    ENABLE_EDGAR_INTEGRATION = os.getenv("ENABLE_EDGAR_INTEGRATION", "false").lower() == "true"


class EdgarConfig:
    """Configuration for SEC EDGAR MCP server integration."""

    # SEC EDGAR API requires a User-Agent header with contact info
    # Format: "CompanyName/Version (contact@email.com)"
    USER_AGENT = os.getenv(
        "SEC_EDGAR_USER_AGENT",
        "FinancialResearchAgent/1.0 (your-email@example.com)",
    )

    # MCP server configuration
    MCP_SERVER_COMMAND = os.getenv("EDGAR_MCP_COMMAND", "uvx")
    MCP_SERVER_ARGS = os.getenv(
        "EDGAR_MCP_ARGS", "sec-edgar-mcp"
    ).split()  # Default: use uvx to run the package

    # Alternative: Docker-based MCP server
    # MCP_SERVER_COMMAND = "docker"
    # MCP_SERVER_ARGS = ["run", "-i", "--rm", "stefanoamorelli/sec-edgar-mcp:latest"]

    # Tool filtering - only enable specific EDGAR tools
    # Set to None to enable all tools
    ALLOWED_EDGAR_TOOLS = os.getenv("EDGAR_ALLOWED_TOOLS")
    if ALLOWED_EDGAR_TOOLS:
        ALLOWED_EDGAR_TOOLS = [t.strip() for t in ALLOWED_EDGAR_TOOLS.split(",")]

    # Example allowed tools:
    # - get_company_facts
    # - get_recent_filings
    # - get_filing_content
    # - search_10k
    # - search_10q
    # - get_financial_statements
    # - get_insider_transactions

    @classmethod
    def get_mcp_env(cls) -> dict[str, str]:
        """Get environment variables for the MCP server."""
        env = os.environ.copy()
        env["SEC_EDGAR_USER_AGENT"] = cls.USER_AGENT
        return env

    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required EDGAR configuration is present."""
        if not cls.USER_AGENT or cls.USER_AGENT == "FinancialResearchAgent/1.0 (your-email@example.com)":
            return False
        return True


# Validate EDGAR config on import if enabled
if AgentConfig.ENABLE_EDGAR_INTEGRATION:
    if not EdgarConfig.validate_config():
        import warnings

        warnings.warn(
            "SEC EDGAR integration is enabled but SEC_EDGAR_USER_AGENT is not properly configured. "
            "Please set it to 'CompanyName/Version (contact@email.com)' format. "
            "See: https://www.sec.gov/os/accessing-edgar-data"
        )
