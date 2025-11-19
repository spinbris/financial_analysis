#!/usr/bin/env python3
"""
Launch script for Financial Research Agent Web Interface with Authentication.

This script starts the Gradio web interface with FastAPI backend
for handling Supabase magic link OAuth callbacks.

Run: python launch_web_app_with_auth.py
Access: http://localhost:7860
"""

import sys
import os
import uvicorn
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from financial_research_agent/.env
env_path = Path(__file__).parent / "financial_research_agent" / ".env"
load_dotenv(env_path)

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
import gradio as gr

from financial_research_agent.web_app import WebApp


def create_app():
    """Create FastAPI app with Gradio mounted and auth callback route."""

    # Get Supabase credentials for login page
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_ANON_KEY", "")

    # Create FastAPI app
    fastapi_app = FastAPI(
        title="Financial Research Agent",
        description="AI-powered financial analysis with Supabase authentication"
    )

    # Login page route
    @fastapi_app.get("/login")
    async def login_page(request: Request):
        """Show login page with magic link form."""
        return HTMLResponse(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Sign In - Financial Research Agent</title>
                <style>
                    * {{
                        box-sizing: border-box;
                    }}
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        min-height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }}
                    .container {{
                        background: white;
                        padding: 48px;
                        border-radius: 16px;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                        text-align: center;
                        max-width: 420px;
                        width: 90%;
                    }}
                    .logo {{
                        font-size: 48px;
                        margin-bottom: 16px;
                    }}
                    h1 {{
                        color: #1a1d1f;
                        margin: 0 0 8px 0;
                        font-size: 24px;
                    }}
                    .subtitle {{
                        color: #6b7280;
                        margin-bottom: 32px;
                        font-size: 14px;
                    }}
                    .form-group {{
                        text-align: left;
                        margin-bottom: 16px;
                    }}
                    label {{
                        display: block;
                        color: #374151;
                        font-weight: 500;
                        margin-bottom: 8px;
                        font-size: 14px;
                    }}
                    input[type="email"] {{
                        width: 100%;
                        padding: 12px 16px;
                        border: 2px solid #e5e7eb;
                        border-radius: 8px;
                        font-size: 16px;
                        transition: border-color 0.2s;
                    }}
                    input[type="email"]:focus {{
                        outline: none;
                        border-color: #0066cc;
                    }}
                    button {{
                        width: 100%;
                        padding: 14px 24px;
                        background: #0066cc;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        font-size: 16px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: background 0.2s;
                        margin-top: 8px;
                    }}
                    button:hover {{
                        background: #0052a3;
                    }}
                    button:disabled {{
                        background: #9ca3af;
                        cursor: not-allowed;
                    }}
                    .message {{
                        margin-top: 16px;
                        padding: 12px;
                        border-radius: 8px;
                        font-size: 14px;
                    }}
                    .message.success {{
                        background: #d1fae5;
                        color: #065f46;
                    }}
                    .message.error {{
                        background: #fee2e2;
                        color: #991b1b;
                    }}
                    .footer {{
                        margin-top: 24px;
                        font-size: 12px;
                        color: #9ca3af;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="logo">📊</div>
                    <h1>Financial Research Agent</h1>
                    <p class="subtitle">Investment-Grade Analysis Powered by SEC EDGAR</p>

                    <form id="login-form">
                        <div class="form-group">
                            <label for="email">Email Address</label>
                            <input type="email" id="email" name="email" placeholder="your@email.com" required>
                        </div>
                        <button type="submit" id="submit-btn">Send Magic Link</button>
                    </form>

                    <div id="message" class="message" style="display: none;"></div>

                    <p class="footer">
                        Free to use. Email only used for access and usage tracking.<br>
                        We'll send you a secure link to sign in.
                    </p>
                </div>

                <script src="https://unpkg.com/@supabase/supabase-js@2"></script>
                <script>
                    const supabaseUrl = '{supabase_url}';
                    const supabaseKey = '{supabase_key}';
                    const supabase = window.supabase.createClient(supabaseUrl, supabaseKey);

                    // Check if already authenticated
                    (async () => {{
                        const {{ data: {{ session }} }} = await supabase.auth.getSession();
                        if (session) {{
                            window.location.href = '/app';
                        }}
                    }})();

                    document.getElementById('login-form').addEventListener('submit', async (e) => {{
                        e.preventDefault();

                        const email = document.getElementById('email').value;
                        const btn = document.getElementById('submit-btn');
                        const msg = document.getElementById('message');

                        btn.disabled = true;
                        btn.textContent = 'Sending...';

                        try {{
                            const {{ error }} = await supabase.auth.signInWithOtp({{
                                email: email,
                                options: {{
                                    emailRedirectTo: window.location.origin + '/auth/callback'
                                }}
                            }});

                            if (error) throw error;

                            msg.className = 'message success';
                            msg.textContent = 'Check your email for the magic link!';
                            msg.style.display = 'block';
                            btn.textContent = 'Link Sent!';
                        }} catch (error) {{
                            msg.className = 'message error';
                            msg.textContent = error.message;
                            msg.style.display = 'block';
                            btn.disabled = false;
                            btn.textContent = 'Send Magic Link';
                        }}
                    }});
                </script>
            </body>
            </html>
        """)

    # Root route - check auth and redirect
    @fastapi_app.get("/")
    async def root(request: Request):
        """Redirect to login or app based on auth state."""
        # Check for authenticated query param (set by callback)
        if request.query_params.get("authenticated") == "true":
            return RedirectResponse(url="/app", status_code=302)
        # Otherwise redirect to login
        return RedirectResponse(url="/login", status_code=302)

    # Auth callback route - must be defined before mounting Gradio
    @fastapi_app.get("/auth/callback")
    async def auth_callback(request: Request):
        """
        Handle Supabase magic link callback.

        Supabase sends tokens in URL fragment (after #).
        We need JavaScript to extract them since fragments aren't sent to server.
        """
        # Check for error in query params
        error = request.query_params.get("error")
        if error:
            error_description = request.query_params.get(
                "error_description", "Unknown error"
            )
            return HTMLResponse(f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Authentication Error</title>
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            min-height: 100vh;
                            margin: 0;
                            background: #f5f7fa;
                        }}
                        .container {{
                            background: white;
                            padding: 40px;
                            border-radius: 12px;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                            text-align: center;
                            max-width: 400px;
                        }}
                        h1 {{ color: #dc2626; margin-bottom: 16px; }}
                        p {{ color: #6b7280; }}
                        a {{
                            display: inline-block;
                            margin-top: 20px;
                            padding: 12px 24px;
                            background: #0066cc;
                            color: white;
                            text-decoration: none;
                            border-radius: 8px;
                        }}
                        a:hover {{ background: #0052a3; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Authentication Error</h1>
                        <p>{error_description}</p>
                        <a href="/login">Return to login</a>
                    </div>
                </body>
                </html>
            """)

        # Check if tokens are in query params (PKCE flow)
        access_token = request.query_params.get("access_token")
        refresh_token = request.query_params.get("refresh_token")

        if access_token:
            # Tokens received as query params - store and redirect
            return HTMLResponse(f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Authenticating...</title>
                    <script>
                        // Store tokens in localStorage
                        localStorage.setItem('supabase_access_token', '{access_token}');
                        localStorage.setItem('supabase_refresh_token', '{refresh_token}');
                        // Redirect to main app
                        window.location.href = '/app';
                    </script>
                </head>
                <body>
                    <p>Authenticating... You will be redirected shortly.</p>
                </body>
                </html>
            """)
        else:
            # Tokens in URL fragment - need JavaScript to extract
            return HTMLResponse("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Authenticating...</title>
                    <style>
                        body {
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            min-height: 100vh;
                            margin: 0;
                            background: #f5f7fa;
                        }
                        .container {
                            background: white;
                            padding: 40px;
                            border-radius: 12px;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                            text-align: center;
                        }
                        .spinner {
                            width: 40px;
                            height: 40px;
                            border: 4px solid #e5e7eb;
                            border-top: 4px solid #0066cc;
                            border-radius: 50%;
                            animation: spin 1s linear infinite;
                            margin: 0 auto 20px;
                        }
                        @keyframes spin {
                            0% { transform: rotate(0deg); }
                            100% { transform: rotate(360deg); }
                        }
                    </style>
                    <script>
                        // Extract tokens from URL fragment
                        const hash = window.location.hash.substring(1);
                        const params = new URLSearchParams(hash);

                        const accessToken = params.get('access_token');
                        const refreshToken = params.get('refresh_token');

                        if (accessToken) {
                            // Store tokens in localStorage
                            localStorage.setItem('supabase_access_token', accessToken);
                            localStorage.setItem('supabase_refresh_token', refreshToken);
                            // Redirect to main app
                            window.location.href = '/app';
                        } else {
                            // No tokens found
                            document.body.innerHTML = `
                                <div class="container">
                                    <h1>Authentication Failed</h1>
                                    <p>No authentication tokens received.</p>
                                    <a href="/login" style="display:inline-block;margin-top:20px;padding:12px 24px;background:#0066cc;color:white;text-decoration:none;border-radius:8px;">Try Again</a>
                                </div>
                            `;
                        }
                    </script>
                </head>
                <body>
                    <div class="container">
                        <div class="spinner"></div>
                        <p>Processing authentication...</p>
                    </div>
                </body>
                </html>
            """)

    # Create Gradio web app
    web_app_instance = WebApp()
    gradio_app = web_app_instance.create_interface()

    # Mount Gradio app at /app (requires authentication)
    fastapi_app = gr.mount_gradio_app(
        fastapi_app,
        gradio_app,
        path="/app"
    )

    return fastapi_app


def main():
    """Main entry point."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     📊 FINANCIAL RESEARCH AGENT - WEB INTERFACE              ║
║                                                               ║
║     Investment-Grade Financial Analysis                       ║
║     Powered by SEC EDGAR                                      ║
║     🔐 Authentication Enabled (Supabase)                      ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

Starting web server with authentication...

The interface will open in your default browser.
If it doesn't open automatically, navigate to: http://localhost:7860

Press Ctrl+C to stop the server.
""")

    # Check for Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        print("""
⚠️  WARNING: Supabase credentials not found!

To enable authentication, add to your .env file:
  SUPABASE_URL=https://xxxxx.supabase.co
  SUPABASE_ANON_KEY=eyJhbGciOi...

Authentication features will be disabled until configured.
""")

    # Create and run app
    app = create_app()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=7860,
        log_level="info"
    )


if __name__ == "__main__":
    main()
