"""
LLM Provider Management with Session-based API Keys.

This module provides:
1. Session-based API key management (in-memory only, never persisted)
2. Groq + OpenAI LLM provider selection with automatic fallback
3. User-provided API keys with clear security instructions
"""

import os
import secrets
import time
from dataclasses import dataclass, field
from typing import Optional, Literal
from datetime import datetime, timedelta

import openai

# Make groq import optional (only needed if using Groq provider)
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


# Provider types
LLMProvider = Literal["groq", "openai"]


@dataclass
class SessionKeys:
    """API keys for a user session (in-memory only)."""

    session_id: str
    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))

    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.now() > self.expires_at

    def has_key(self, provider: LLMProvider) -> bool:
        """Check if session has a key for the specified provider."""
        if provider == "groq":
            return self.groq_api_key is not None
        elif provider == "openai":
            return self.openai_api_key is not None
        return False


class SessionKeyManager:
    """
    Manage API keys per session (in-memory only, never persisted to disk).

    Security features:
    - Keys stored in memory only (never written to disk)
    - Automatic expiration after 24 hours
    - Overwrite keys with random data before deletion
    - Clear user instructions to delete keys from provider
    """

    def __init__(self):
        # In-memory storage only
        self._sessions: dict[str, SessionKeys] = {}

    def create_session(self) -> str:
        """Create a new session and return session ID."""
        session_id = secrets.token_urlsafe(32)
        self._sessions[session_id] = SessionKeys(session_id=session_id)
        return session_id

    def set_api_key(
        self,
        session_id: str,
        provider: LLMProvider,
        api_key: str
    ) -> None:
        """Store API key for a session (in-memory only)."""
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionKeys(session_id=session_id)

        session = self._sessions[session_id]

        if provider == "groq":
            session.groq_api_key = api_key
        elif provider == "openai":
            session.openai_api_key = api_key

    def get_api_key(
        self,
        session_id: str,
        provider: LLMProvider
    ) -> Optional[str]:
        """Retrieve API key for a session."""
        session = self._sessions.get(session_id)

        if not session or session.is_expired():
            # Auto-cleanup expired session
            if session:
                self._secure_delete_session(session_id)
            return None

        if provider == "groq":
            return session.groq_api_key
        elif provider == "openai":
            return session.openai_api_key

        return None

    def clear_session(self, session_id: str) -> None:
        """Delete all keys for a session (secure deletion)."""
        self._secure_delete_session(session_id)

    def _secure_delete_session(self, session_id: str) -> None:
        """Securely delete session by overwriting keys with random data."""
        if session_id in self._sessions:
            session = self._sessions[session_id]

            # Overwrite keys with random data before deletion
            if session.groq_api_key:
                session.groq_api_key = secrets.token_urlsafe(64)
            if session.openai_api_key:
                session.openai_api_key = secrets.token_urlsafe(64)

            # Delete session
            del self._sessions[session_id]

    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions. Returns number of sessions cleaned up."""
        expired = [
            sid for sid, session in self._sessions.items()
            if session.is_expired()
        ]

        for sid in expired:
            self._secure_delete_session(sid)

        return len(expired)


# Global session manager instance
_session_manager = SessionKeyManager()


def get_session_manager() -> SessionKeyManager:
    """Get the global session key manager."""
    return _session_manager


# Groq model configurations
# Updated models as of November 2025
# IMPORTANT: Agent SDK requires json_schema support for structured outputs
# Standard Llama models do NOT support json_schema
# Only OpenAI GPT-OSS models on Groq support structured outputs
GROQ_MODELS = {
    "gpt-oss-120b": {
        "name": "openai/gpt-oss-120b",
        "input_cost": 0.10,  # per 1M tokens (estimated)
        "output_cost": 0.10,  # per 1M tokens (estimated)
        "context_window": 128000,
        "description": "Supports json_schema, best quality"
    },
    "gpt-oss-20b": {
        "name": "openai/gpt-oss-20b",
        "input_cost": 0.05,  # per 1M tokens (estimated)
        "output_cost": 0.05,  # per 1M tokens (estimated)
        "context_window": 128000,
        "description": "Supports json_schema, faster"
    },
    # Note: These models do NOT support json_schema (kept for reference)
    "llama-3.3-70b": {
        "name": "llama-3.3-70b-versatile",
        "input_cost": 0.05,  # per 1M tokens
        "output_cost": 0.08,  # per 1M tokens
        "context_window": 128000,
        "description": "NO json_schema support"
    },
    "llama-3.1-8b": {
        "name": "llama-3.1-8b-instant",
        "input_cost": 0.05,  # per 1M tokens
        "output_cost": 0.08,  # per 1M tokens
        "context_window": 128000,
        "description": "NO json_schema support"
    }
}

# Default model selections per task
# Agent SDK requires json_schema support, so we must use gpt-oss models
DEFAULT_GROQ_MODELS = {
    "planner": "gpt-oss-120b",     # Needs json_schema
    "search": "gpt-oss-120b",      # Needs json_schema
    "writer": "gpt-oss-120b",      # Needs json_schema
    "verifier": "gpt-oss-120b",    # Needs json_schema
    "edgar": "gpt-oss-120b",       # Needs json_schema
    "financials": "gpt-oss-120b",  # Needs json_schema
    "risk": "gpt-oss-120b",        # Needs json_schema
    "metrics": "gpt-oss-120b"      # Needs json_schema
}


def get_groq_model(task: str = "default") -> str:
    """Get the Groq model name for a specific task."""
    model_key = DEFAULT_GROQ_MODELS.get(task, "gpt-oss-120b")
    return GROQ_MODELS[model_key]["name"]


def configure_llm_provider(
    provider: LLMProvider = "groq",
    session_id: Optional[str] = None,
    groq_api_key: Optional[str] = None,
    openai_api_key: Optional[str] = None
) -> tuple[LLMProvider, str]:
    """
    Configure LLM provider with fallback logic.

    Priority order:
    1. User-provided session key (if session_id provided)
    2. Explicitly provided API key (if groq_api_key/openai_api_key provided)
    3. Environment variable
    4. Fallback to other provider

    Returns:
        (provider, api_key) tuple

    Raises:
        ValueError: If no API key available for any provider
    """
    # If Groq is requested but not available, force fallback to OpenAI
    if provider == "groq" and not GROQ_AVAILABLE:
        provider = "openai"

    manager = get_session_manager()

    # Try primary provider
    api_key = None

    # 1. Try session key
    if session_id:
        api_key = manager.get_api_key(session_id, provider)

    # 2. Try explicitly provided key
    if not api_key:
        if provider == "groq" and groq_api_key:
            api_key = groq_api_key
        elif provider == "openai" and openai_api_key:
            api_key = openai_api_key

    # 3. Try environment variable
    if not api_key:
        env_var = "GROQ_API_KEY" if provider == "groq" else "OPENAI_API_KEY"
        api_key = os.getenv(env_var)

    # If primary provider has key, use it
    if api_key:
        return provider, api_key

    # 4. Fallback to other provider
    fallback_provider: LLMProvider = "openai" if provider == "groq" else "groq"

    # Try fallback session key
    if session_id:
        api_key = manager.get_api_key(session_id, fallback_provider)

    # Try fallback explicit key
    if not api_key:
        if fallback_provider == "groq" and groq_api_key:
            api_key = groq_api_key
        elif fallback_provider == "openai" and openai_api_key:
            api_key = openai_api_key

    # Try fallback environment variable
    if not api_key:
        env_var = "GROQ_API_KEY" if fallback_provider == "groq" else "OPENAI_API_KEY"
        api_key = os.getenv(env_var)

    if api_key:
        return fallback_provider, api_key

    # No API key available
    raise ValueError(
        f"No API key available for {provider} or fallback provider {fallback_provider}. "
        f"Please provide an API key via session, parameter, or environment variable."
    )


def get_model_name(
    provider: LLMProvider,
    task: str = "default",
    openai_model: Optional[str] = None
) -> str:
    """
    Get the appropriate model name for a provider and task.

    Args:
        provider: LLM provider ("groq" or "openai")
        task: Task type (planner, search, writer, etc.)
        openai_model: Specific OpenAI model name (if provider is openai)

    Returns:
        Model name string
    """
    if provider == "groq":
        return get_groq_model(task)
    else:
        # Use provided OpenAI model or default from config
        if openai_model:
            return openai_model
        # Import here to avoid circular dependency
        from financial_research_agent.config import AgentConfig

        # Map task to config attribute
        task_map = {
            "planner": AgentConfig.PLANNER_MODEL,
            "search": AgentConfig.SEARCH_MODEL,
            "writer": AgentConfig.WRITER_MODEL,
            "verifier": AgentConfig.VERIFIER_MODEL,
            "edgar": AgentConfig.EDGAR_MODEL,
            "financials": AgentConfig.FINANCIALS_MODEL,
            "risk": AgentConfig.RISK_MODEL,
            "metrics": AgentConfig.METRICS_MODEL
        }

        return task_map.get(task, "gpt-4o")


def create_openai_client(
    provider: LLMProvider = "groq",
    session_id: Optional[str] = None,
    groq_api_key: Optional[str] = None,
    openai_api_key: Optional[str] = None
) -> tuple[openai.OpenAI, LLMProvider]:
    """
    Create an OpenAI-compatible client for the specified provider.

    Groq is OpenAI-compatible, so we can use OpenAI client with Groq base URL.

    Returns:
        (client, actual_provider) tuple
    """
    actual_provider, api_key = configure_llm_provider(
        provider=provider,
        session_id=session_id,
        groq_api_key=groq_api_key,
        openai_api_key=openai_api_key
    )

    if actual_provider == "groq":
        # Create OpenAI client with Groq base URL
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
    else:
        # Standard OpenAI client
        client = openai.OpenAI(api_key=api_key)

    return client, actual_provider


# User instructions for API key security
API_KEY_SECURITY_INSTRUCTIONS = """
**IMPORTANT: API Key Security Instructions**

Your API keys are stored in-memory ONLY for the duration of this session (maximum 24 hours).

**After you're done using this tool:**

1. **Groq API Key**: Log into https://console.groq.com/keys and DELETE the API key you provided
2. **OpenAI API Key**: Log into https://platform.openai.com/api-keys and DELETE the API key you provided

**Why delete the keys?**
- Your keys are NOT saved to disk or any database
- They exist in memory only during your session
- However, for maximum security, we recommend deleting keys from the provider after use
- You can always create new keys for future sessions

**Key Expiration:**
- Session keys automatically expire after 24 hours
- Keys are securely overwritten with random data before deletion
"""


def get_api_key_instructions() -> str:
    """Get user-friendly API key security instructions."""
    return API_KEY_SECURITY_INSTRUCTIONS
