from edgar import Company, set_identity

set_identity("Steve Parton steve@sjpconsulting.com")

company = Company("AAPL")
financials = company.get_financials()
bs = financials.balance_sheet()

print("Exploring Statement Object API\n" + "="*60)

# 1. What type is it?
print(f"\nType: {type(bs)}")

# 2. What attributes/methods does it have?
print(f"\nAvailable attributes/methods:")
attrs = [a for a in dir(bs) if not a.startswith('_')]
for attr in attrs[:15]:  # Show first 15
    print(f"  - {attr}")

# 3. Can we convert to dict or DataFrame?
print("\n" + "="*60)
print("Testing data access methods:\n")

if hasattr(bs, 'to_dict'):
    print("✓ Has to_dict() method")
    data = bs.to_dict()
    print(f"  Keys: {list(data.keys())[:5]}...")  # First 5 keys

if hasattr(bs, 'to_dataframe'):
    print("✓ Has to_dataframe() method")
    
if hasattr(bs, 'data'):
    print("✓ Has data attribute")
    print(f"  Type: {type(bs.data)}")

if hasattr(bs, 'facts'):
    print("✓ Has facts attribute")
    
if hasattr(bs, 'get'):
    print("✓ Has get() method (dict-like)")

# 4. Try accessing as dict
print("\n" + "="*60)
print("Testing direct access:\n")

try:
    # Try dict-like access
    if hasattr(bs, '__getitem__'):
        print("✓ Supports dict-like access: bs['Assets']")
except Exception as e:
    print(f"✗ Dict access failed: {e}")

# 5. Check the actual string representation
print("\n" + "="*60)
print("String representation preview:")
print(str(bs)[:500])  # First 500 chars

print("\n" + "="*60)
