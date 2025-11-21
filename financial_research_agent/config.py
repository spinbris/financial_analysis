"""Configuration for the financial research agent."""

import os
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=True)
except ImportError:
    pass  # python-dotenv not installed, will use environment variables only

# OpenAI configuration


class AgentConfig:
    """Configuration for agent models and settings."""

    # Model Configuration
    # All models use OpenAI API
    # Current cost: ~$0.50/report (see COST_OPTIMIZATION_ANALYSIS.md for details)
    # Override individual models via environment variables

    PLANNER_MODEL = os.getenv("PLANNER_MODEL", "o3-mini")
    SEARCH_MODEL = os.getenv("SEARCH_MODEL", "gpt-4.1")
    WRITER_MODEL = os.getenv("WRITER_MODEL", "gpt-5.1")
    VERIFIER_MODEL = os.getenv("VERIFIER_MODEL", "gpt-4.1")
    EDGAR_MODEL = os.getenv("EDGAR_MODEL", "gpt-4.1")
    FINANCIALS_MODEL = os.getenv("FINANCIALS_MODEL", "gpt-5")
    RISK_MODEL = os.getenv("RISK_MODEL", "gpt-5")
    METRICS_MODEL = os.getenv("METRICS_MODEL", "gpt-5")

    # Reasoning effort per model (minimal, low, medium, high)
    # Only applies when using gpt-5, gpt-5-mini, or gpt-5-nano models
    # Note: o3-mini only supports "low", "medium", "high" (not "minimal")
    # "minimal" = fast (few/no reasoning tokens), "high" = slow but highest quality
    PLANNER_REASONING_EFFORT = os.getenv("PLANNER_REASONING_EFFORT", "low")
    SEARCH_REASONING_EFFORT = os.getenv("SEARCH_REASONING_EFFORT", "minimal")
    EDGAR_REASONING_EFFORT = os.getenv("EDGAR_REASONING_EFFORT", "minimal")
    METRICS_REASONING_EFFORT = os.getenv("METRICS_REASONING_EFFORT", "minimal")
    FINANCIALS_REASONING_EFFORT = os.getenv("FINANCIALS_REASONING_EFFORT", "low")
    RISK_REASONING_EFFORT = os.getenv("RISK_REASONING_EFFORT", "low")
    WRITER_REASONING_EFFORT = os.getenv("WRITER_REASONING_EFFORT", "low")
    VERIFIER_REASONING_EFFORT = os.getenv("VERIFIER_REASONING_EFFORT", "minimal")

    # Search configuration
    MAX_SEARCH_RETRIES = int(os.getenv("MAX_SEARCH_RETRIES", "3"))
    SEARCH_RETRY_DELAY = float(os.getenv("SEARCH_RETRY_DELAY", "2.0"))

    # Agent execution configuration
    MAX_AGENT_TURNS = int(os.getenv("MAX_AGENT_TURNS", "25"))
    """Maximum number of turns (tool calls) an agent can make in a single run.
    Default is 25. Financial metrics agent may need 15-20 turns for complex queries."""

    # Output configuration
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "financial_research_agent/output")

    # Feature flags
    ENABLE_EDGAR_INTEGRATION = os.getenv("ENABLE_EDGAR_INTEGRATION", "false").lower() == "true"

    @staticmethod
    def get_model_settings(model: str, reasoning_effort: str):
        """
        Get ModelSettings for a given model and reasoning effort.

        Only applies to reasoning models: gpt-5, gpt-5-mini, gpt-5-nano, o1, o3, o3-mini.
        Returns None for other models (gpt-4o, gpt-4o-mini, etc.).

        Args:
            model: Model name (e.g., "gpt-5", "o3-mini", "gpt-4o")
            reasoning_effort: Effort level ("minimal", "low", "medium", "high")

        Returns:
            ModelSettings if reasoning model, None otherwise
        """
        # Only apply reasoning settings to reasoning models
        is_reasoning_model = (
            model.startswith("gpt-5") or
            model.startswith("o1") or
            model.startswith("o3")
        )

        if not is_reasoning_model:
            return None

        try:
            from agents import ModelSettings
            from openai.types.shared import Reasoning

            # o3 models only support verbosity="medium"
            # gpt-5 models support verbosity="low", "medium", or "high"
            verbosity = "medium" if model.startswith("o") else "low"

            return ModelSettings(
                reasoning=Reasoning(effort=reasoning_effort),
                verbosity=verbosity
            )
        except ImportError:
            # If agents SDK not available, return None
            return None


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
