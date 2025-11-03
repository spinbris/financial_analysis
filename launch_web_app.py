#!/usr/bin/env python3
"""
Launch script for Financial Research Agent Web Interface.

This script starts the Gradio web interface on http://localhost:7860
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

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
