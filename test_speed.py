#!/usr/bin/env python3
"""
Test cache performance: Compare download speed vs cache retrieval.

This simulates the performance difference between:
1. Downloading from SEC (slow)
2. Loading from SQLite cache (fast)

Usage:
    uv run python test_speed.py
"""

import time
import sqlite3
from pathlib import Path

def measure_download_simulation():
    """Simulate downloading from SEC (slow operation)."""
    print("⏱️  Simulating SEC Download...")
    
    # Simulate network latency + download time
    # Real SEC downloads typically take 3-5 seconds
    start = time.time()
    
    # Simulate parsing HTML/XML
    time.sleep(0.5)
    
    # Simulate downloading financials
    time.sleep(1.5)
    
    # Simulate parsing XBRL
    time.sleep(1.0)
    
    # Simulate extracting data
    time.sleep(0.5)
    
    elapsed = time.time() - start
    
    print(f"   Download completed in {elapsed:.2f}s")
    return elapsed

def measure_cache_retrieval():
    """Measure SQLite cache retrieval speed."""
    print("⚡ Loading from SQLite Cache...")
    
    cache_dir = Path("data/sec_cache")
    db_path = cache_dir / "test_financials.db"
    
    if not db_path.exists():
        print("   ⚠️  Cache database not found. Run test_cache_quick.py first!")
        return None
    
    start = time.time()
    
    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Query filing metadata
    cursor.execute("""
        SELECT id, ticker, form_type, filing_date
        FROM filings_metadata
        WHERE ticker = 'AAPL'
        LIMIT 1
    """)
    filing = cursor.fetchone()
    
    if not filing:
        print("   ⚠️  No AAPL data in cache. Run test_cache_quick.py first!")
        conn.close()
        return None
    
    filing_id = filing[0]
    
    # Query balance sheet items
    cursor.execute("""
        SELECT concept, label, value
        FROM balance_sheet
        WHERE filing_id = ?
    """, (filing_id,))
    
    items = cursor.fetchall()
    
    conn.close()
    
    elapsed = time.time() - start
    
    print(f"   Retrieved {len(items)} items in {elapsed:.4f}s")
    return elapsed

def test_cache_performance():
    """Compare cache vs download performance."""
    
    print("🚀 Testing Cache Performance")
    print("=" * 60)
    
    # Test 1: Simulated download
    print("\n1️⃣  Test: Download from SEC (simulated)")
    download_time = measure_download_simulation()
    
    # Test 2: Cache retrieval
    print("\n2️⃣  Test: Load from SQLite Cache")
    cache_time = measure_cache_retrieval()
    
    if cache_time is None:
        print("\n❌ Could not test cache. Run test_cache_quick.py first!")
        return False
    
    # Calculate speedup
    print("\n" + "=" * 60)
    print("📊 Performance Comparison:")
    print(f"   Download from SEC:  {download_time:.2f}s")
    print(f"   Load from Cache:    {cache_time:.4f}s")
    
    speedup = download_time / cache_time
    print(f"\n   🚀 Speedup: {speedup:.1f}x faster!")
    
    time_saved = download_time - cache_time
    print(f"   ⏱️  Time Saved: {time_saved:.2f}s per query")
    
    # Calculate savings for multiple queries
    queries_per_day = [10, 50, 100]
    print(f"\n💰 Time Savings Over Time:")
    for queries in queries_per_day:
        total_saved = time_saved * queries
        minutes_saved = total_saved / 60
        print(f"   {queries:3d} queries/day: {minutes_saved:.1f} minutes saved")
    
    # Real-world context
    print("\n🎯 Real-World Performance:")
    print("   Without cache: 3-5 seconds per query")
    print("   With cache:    0.01-0.05 seconds per query")
    print("   Expected speedup: 100-400x faster! 🚀")
    
    print("\n" + "=" * 60)
    print("✅ Cache performance test complete!")
    
    return True

if __name__ == "__main__":
    try:
        test_cache_performance()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
