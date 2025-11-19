"""
Supabase authentication integration.
Handles user sign-in, session management, and user data.
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from supabase import create_client, Client
except ImportError:
    raise ImportError("Please install supabase: pip install supabase>=2.0.0")


class SupabaseAuth:
    """Handle user authentication with Supabase."""

    def __init__(self):
        """Initialize Supabase client."""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")

        if not url or not key:
            raise ValueError(
                "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_ANON_KEY"
            )

        self.client: Client = create_client(url, key)

    def send_magic_link(self, email: str) -> Dict[str, Any]:
        """
        Send magic link to user's email.

        Args:
            email: User's email address

        Returns:
            Dict with success status and message
        """
        try:
            response = self.client.auth.sign_in_with_otp({
                "email": email,
                "options": {
                    "email_redirect_to": os.getenv(
                        "AUTH_REDIRECT_URL",
                        "http://localhost:7860/auth/callback"
                    )
                }
            })

            return {
                "success": True,
                "message": f"Magic link sent to {email}. Check your inbox!"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }

    def verify_token(self, token: str, token_hash: Optional[str] = None) -> Optional[Dict]:
        """
        Verify magic link token.

        Args:
            token: Token from magic link URL
            token_hash: Optional token hash for PKCE flow

        Returns:
            User data if valid, None otherwise
        """
        try:
            # For email OTP verification
            if token_hash:
                response = self.client.auth.verify_otp({
                    "token_hash": token_hash,
                    "type": "email"
                })
            else:
                response = self.client.auth.verify_otp({
                    "token": token,
                    "type": "magiclink"
                })

            if response and response.user:
                # Ensure user exists in users table
                self._ensure_user_record(response.user)
                return {
                    "user": response.user,
                    "session": response.session
                }
            return None
        except Exception as e:
            print(f"Token verification failed: {e}")
            return None

    def get_user(self, access_token: str) -> Optional[Dict]:
        """
        Get current user from access token.

        Args:
            access_token: User's session token

        Returns:
            User data if valid session
        """
        try:
            response = self.client.auth.get_user(access_token)
            return response.user
        except Exception as e:
            print(f"Failed to get user: {e}")
            return None

    def get_session(self) -> Optional[Dict]:
        """
        Get current session.

        Returns:
            Session data if exists
        """
        try:
            response = self.client.auth.get_session()
            return response
        except Exception as e:
            print(f"Failed to get session: {e}")
            return None

    def set_session(self, access_token: str, refresh_token: str) -> Optional[Dict]:
        """
        Set session with tokens.

        Args:
            access_token: Access token from callback
            refresh_token: Refresh token from callback

        Returns:
            Session data if successful
        """
        try:
            response = self.client.auth.set_session(access_token, refresh_token)
            return response
        except Exception as e:
            print(f"Failed to set session: {e}")
            return None

    def sign_out(self) -> bool:
        """
        Sign out current user.

        Returns:
            True if successful
        """
        try:
            self.client.auth.sign_out()
            return True
        except Exception as e:
            print(f"Sign out failed: {e}")
            return False

    def _ensure_user_record(self, user) -> None:
        """
        Ensure user exists in users table after authentication.

        Args:
            user: Supabase user object
        """
        try:
            # Check if user exists
            existing = self.client.table("users").select("id").eq("id", user.id).execute()

            if not existing.data:
                # Create user record
                self.client.table("users").insert({
                    "id": user.id,
                    "email": user.email,
                    "metadata": {},
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }).execute()
        except Exception as e:
            print(f"Failed to ensure user record: {e}")

    def save_user_metadata(self, user_id: str, metadata: Dict) -> bool:
        """
        Save user preferences/metadata.

        Args:
            user_id: User's ID
            metadata: Dict of preferences (e.g., favorite tickers)

        Returns:
            True if successful
        """
        try:
            self.client.table("users").upsert({
                "id": user_id,
                "metadata": metadata,
                "updated_at": datetime.utcnow().isoformat()
            }).execute()
            return True
        except Exception as e:
            print(f"Failed to save metadata: {e}")
            return False

    def get_user_metadata(self, user_id: str) -> Optional[Dict]:
        """
        Get user preferences/metadata.

        Args:
            user_id: User's ID

        Returns:
            User metadata dict or None
        """
        try:
            response = self.client.table("users").select("*").eq("id", user_id).execute()
            if response.data:
                return response.data[0].get("metadata", {})
            return None
        except Exception as e:
            print(f"Failed to get metadata: {e}")
            return None

    def save_analysis(self, user_id: str, ticker: str, report_path: str,
                      executive_summary: str = None, key_metrics: Dict = None) -> bool:
        """
        Save user's analysis record.

        Args:
            user_id: User's ID
            ticker: Stock ticker analyzed
            report_path: Path to the report
            executive_summary: Optional summary text
            key_metrics: Optional metrics dict

        Returns:
            True if successful
        """
        try:
            self.client.table("analyses").insert({
                "user_id": user_id,
                "ticker": ticker,
                "report_path": report_path,
                "executive_summary": executive_summary,
                "key_metrics": key_metrics,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            return True
        except Exception as e:
            print(f"Failed to save analysis: {e}")
            return False

    def get_user_analyses(self, user_id: str, limit: int = 10) -> list:
        """
        Get user's analysis history.

        Args:
            user_id: User's ID
            limit: Max number of analyses to return

        Returns:
            List of analysis records
        """
        try:
            response = self.client.table("analyses")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            return response.data
        except Exception as e:
            print(f"Failed to get analyses: {e}")
            return []
