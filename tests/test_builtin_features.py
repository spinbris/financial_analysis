from edgar import Company, set_identity

set_identity("Steve Parton steve@sjpconsulting.com")

company = Company("AAPL")
financials = company.get_financials()
bs = financials.balance_sheet()

print("Testing Built-in EdgarTools Features\n" + "="*60)

# 1. Calculate ratios (if this works, it's amazing!)
print("\n1. Testing calculate_ratios():")
try:
    ratios = bs.calculate_ratios()
    print("✓ Built-in ratio calculation available!")
    print(ratios)
except Exception as e:
    print(f"  Note: {e}")

# 2. Analyze trends
print("\n2. Testing analyze_trends():")
try:
    trends = bs.analyze_trends()
    print("✓ Built-in trend analysis available!")
    print(trends)
except Exception as e:
    print(f"  Note: {e}")

# 3. Get raw XBRL data
print("\n3. Testing get_raw_data():")
try:
    raw = bs.get_raw_data()
    print(f"✓ Raw XBRL data available!")
    print(f"  Type: {type(raw)}")
    if isinstance(raw, dict):
        print(f"  Keys: {list(raw.keys())[:5]}...")
except Exception as e:
    print(f"  Note: {e}")

print("\n" + "="*60)
