#!/usr/bin/env python3
"""
Quick test script for web app functionality.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        import gradio as gr
        print("  ✅ gradio imported")

        from financial_research_agent.web_app import WebApp, create_theme, QUERY_TEMPLATES
        print("  ✅ web_app modules imported")

        from financial_research_agent.manager_enhanced import EnhancedFinancialResearchManager
        print("  ✅ manager imported")

        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False


def test_theme():
    """Test theme creation."""
    print("\nTesting theme creation...")
    try:
        from financial_research_agent.web_app import create_theme
        theme = create_theme()
        print(f"  ✅ Theme created: {type(theme).__name__}")
        return True
    except Exception as e:
        print(f"  ❌ Theme creation failed: {e}")
        return False


def test_interface_creation():
    """Test interface creation."""
    print("\nTesting interface creation...")
    try:
        from financial_research_agent.web_app import WebApp
        app = WebApp()
        interface = app.create_interface()
        print(f"  ✅ Interface created: {type(interface).__name__}")
        return True
    except Exception as e:
        print(f"  ❌ Interface creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_templates():
    """Test query templates."""
    print("\nTesting query templates...")
    try:
        from financial_research_agent.web_app import QUERY_TEMPLATES
        print(f"  ✅ {len(QUERY_TEMPLATES)} templates available:")
        for name in list(QUERY_TEMPLATES.keys())[:3]:
            print(f"      - {name}")
        return True
    except Exception as e:
        print(f"  ❌ Templates test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("WEB APP FUNCTIONALITY TEST")
    print("="*60)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("Theme", test_theme()))
    results.append(("Templates", test_templates()))
    results.append(("Interface", test_interface_creation()))

    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:.<40} {status}")

    all_passed = all(result[1] for result in results)

    print("="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("\nYou can now launch the web app:")
        print("  .venv/bin/python launch_web_app.py")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease fix the errors above before launching.")
    print("="*60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
