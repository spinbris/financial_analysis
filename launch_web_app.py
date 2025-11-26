#!/usr/bin/env python3
"""
Launch script for Financial Research Agent Web Interface.

This script starts the Gradio web interface on http://localhost:7860
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load .env from project root BEFORE importing modules that use config
from dotenv import load_dotenv
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)
    print(f"✅ Loaded environment from {env_path}")
    # Verify EDGAR is enabled
    if os.getenv("ENABLE_EDGAR_INTEGRATION", "false").lower() == "true":
        print("✅ EDGAR integration is ENABLED")
    else:
        print("⚠️  EDGAR integration is DISABLED")
else:
    print(f"⚠️  No .env file found at {env_path}")

from financial_research_agent.web_app import main

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     📊 FINANCIAL RESEARCH AGENT - WEB INTERFACE              ║
║                                                               ║
║     Investment-Grade Financial Analysis                       ║
║     Powered by SEC EDGAR                                      ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

Starting web server...

The interface will open in your default browser.
If it doesn't open automatically, navigate to: http://localhost:7860

Press Ctrl+C to stop the server.
""")

    main()
