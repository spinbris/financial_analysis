"""
Gradio authentication UI components.
"""

import gradio as gr
from typing import Optional
import os


class AuthUI:
    """Authentication UI for Gradio."""

    def __init__(self, auth_handler=None):
        """
        Initialize AuthUI.

        Args:
            auth_handler: Optional SupabaseAuth instance (created if not provided)
        """
        self.auth = auth_handler
        self.current_user = None

    def _get_auth(self):
        """Lazy load auth handler."""
        if self.auth is None:
            from financial_research_agent.auth.supabase_auth import SupabaseAuth
            self.auth = SupabaseAuth()
        return self.auth

    def create_login_section(self):
        """Create the login section UI components."""
        with gr.Column():
            gr.Markdown("### Sign In")
            gr.Markdown("Enter your email to receive a magic link")

            email_input = gr.Textbox(
                label="Email",
                placeholder="your@email.com",
                type="email"
            )

            sign_in_btn = gr.Button("Send Magic Link", variant="primary")
            status_msg = gr.Markdown("")

            def handle_sign_in(email):
                if not email or "@" not in email:
                    return "Please enter a valid email address"

                try:
                    auth = self._get_auth()
                    result = auth.send_magic_link(email)

                    if result["success"]:
                        return f"**Magic link sent to {email}**\n\nCheck your inbox and click the link to sign in."
                    else:
                        return f"Error: {result['message']}"
                except Exception as e:
                    return f"Error: {str(e)}"

            sign_in_btn.click(
                fn=handle_sign_in,
                inputs=[email_input],
                outputs=[status_msg]
            )

        return email_input, sign_in_btn, status_msg

    def create_user_panel(self, user_email: str):
        """
        Create panel showing logged-in user info.

        Args:
            user_email: Email of the logged-in user
        """
        with gr.Column():
            gr.Markdown(f"### Signed in as: {user_email}")
            sign_out_btn = gr.Button("Sign Out", variant="secondary")

            status_output = gr.Markdown("")

            def handle_sign_out():
                try:
                    auth = self._get_auth()
                    auth.sign_out()
                    self.current_user = None
                    return "Signed out successfully. Refresh the page to sign in again."
                except Exception as e:
                    return f"Error: {str(e)}"

            sign_out_btn.click(
                fn=handle_sign_out,
                outputs=[status_output]
            )

        return sign_out_btn, status_output

    def create_auth_guard(self, protected_content_fn):
        """
        Create an auth guard that shows content only when authenticated.

        Args:
            protected_content_fn: Function that returns Gradio components for authenticated users

        Returns:
            Gradio component that checks auth state
        """
        with gr.Column() as container:
            # Check if user is authenticated via session
            if self.current_user:
                protected_content_fn(self.current_user)
            else:
                gr.Markdown("Please sign in to access this feature")

        return container


def create_auth_callback_handler():
    """
    Create FastAPI route handler for OAuth callback.

    This is used when mounting Gradio with FastAPI to handle
    the magic link callback URL.

    Returns:
        FastAPI route handler function
    """
    from fastapi import Request
    from fastapi.responses import RedirectResponse, HTMLResponse

    async def auth_callback(request: Request):
        """Handle the magic link callback."""
        # Get tokens from URL fragment or query params
        # Supabase sends tokens as URL fragments, but we need query params

        # Check for error
        error = request.query_params.get("error")
        if error:
            error_description = request.query_params.get("error_description", "Unknown error")
            return HTMLResponse(f"""
                <html>
                <body>
                    <h1>Authentication Error</h1>
                    <p>{error_description}</p>
                    <a href="/">Return to app</a>
                </body>
                </html>
            """)

        # Get the access token and refresh token
        access_token = request.query_params.get("access_token")
        refresh_token = request.query_params.get("refresh_token")
        token_type = request.query_params.get("token_type")

        # If tokens in fragment (client-side), need JavaScript to extract
        # For PKCE flow, tokens come as query params after server exchange

        if access_token:
            # Tokens received - set session and redirect
            # In production, you'd store these in a secure session
            return HTMLResponse(f"""
                <html>
                <head>
                    <script>
                        // Store tokens in localStorage for Gradio to access
                        localStorage.setItem('supabase_access_token', '{access_token}');
                        localStorage.setItem('supabase_refresh_token', '{refresh_token}');
                        // Redirect to main app
                        window.location.href = '/?authenticated=true';
                    </script>
                </head>
                <body>
                    <p>Authenticating... You will be redirected shortly.</p>
                </body>
                </html>
            """)
        else:
            # Handle fragment-based tokens (Supabase default)
            return HTMLResponse("""
                <html>
                <head>
                    <script>
                        // Extract tokens from URL fragment
                        const hash = window.location.hash.substring(1);
                        const params = new URLSearchParams(hash);

                        const accessToken = params.get('access_token');
                        const refreshToken = params.get('refresh_token');

                        if (accessToken) {
                            // Store tokens
                            localStorage.setItem('supabase_access_token', accessToken);
                            localStorage.setItem('supabase_refresh_token', refreshToken);
                            // Redirect to main app
                            window.location.href = '/?authenticated=true';
                        } else {
                            document.body.innerHTML = '<h1>Authentication Failed</h1><p>No tokens received.</p><a href="/">Return to app</a>';
                        }
                    </script>
                </head>
                <body>
                    <p>Processing authentication...</p>
                </body>
                </html>
            """)

    return auth_callback
