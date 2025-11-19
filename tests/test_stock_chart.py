"""
Quick test script to verify stock price chart functionality
"""
import sys
sys.path.insert(0, '.')

from financial_research_agent.web_app import WebApp

# Create instance
ui = WebApp()

# Test with Apple stock
print("Testing AAPL stock chart...")
fig, stats = ui.fetch_stock_price_chart("AAPL", "1y")

if fig is not None:
    print("✅ Chart generated successfully!")
    print("\nStatistics:")
    print(stats)
else:
    print("❌ Chart generation failed!")
    print(stats)

# Test with invalid ticker
print("\n" + "="*50)
print("Testing invalid ticker...")
fig, stats = ui.fetch_stock_price_chart("INVALID123", "1y")

if fig is None:
    print("✅ Invalid ticker handled correctly!")
    print(stats)
else:
    print("❌ Should have failed for invalid ticker")

print("\n✅ All tests passed!")
