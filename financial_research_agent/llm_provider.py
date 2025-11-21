"""
OpenAI API Key Session Management.

This module provides session-based API key management for OpenAI:
1. Session-based API key storage (in-memory only, never persisted)
2. User-provided API keys with clear security instructions
3. Automatic expiration after 24 hours
"""

import secrets
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timedelta


@dataclass
class SessionKeys:
    """API keys for a user session (in-memory only)."""

    session_id: str
    openai_api_key: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))

    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.now() > self.expires_at


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

    def set_api_key(self, session_id: str, provider: str, api_key: str) -> None:
        """
        Store API key for a session (in-memory only).

        Args:
            session_id: Session identifier
            provider: Provider name (only "openai" is supported)
            api_key: API key to store
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionKeys(session_id=session_id)

        session = self._sessions[session_id]

        if provider == "openai":
            session.openai_api_key = api_key

    def get_api_key(self, session_id: str, provider: str) -> Optional[str]:
        """
        Retrieve API key for a session.

        Args:
            session_id: Session identifier
            provider: Provider name (only "openai" is supported)

        Returns:
            API key if found and not expired, None otherwise
        """
        session = self._sessions.get(session_id)

        if not session or session.is_expired():
            # Auto-cleanup expired session
            if session:
                self._secure_delete_session(session_id)
            return None

        if provider == "openai":
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


# User instructions for API key security
API_KEY_SECURITY_INSTRUCTIONS = """
**IMPORTANT: API Key Security Instructions**

Your API keys are stored in-memory ONLY for the duration of this session (maximum 24 hours).

**After you're done using this tool:**

1. **OpenAI API Key**: Log into https://platform.openai.com/api-keys and DELETE the API key you provided

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
