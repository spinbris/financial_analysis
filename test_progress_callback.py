#!/usr/bin/env python3
"""
Quick test to verify progress callback functionality.
This test doesn't run a full analysis - just verifies the callback mechanism works.
"""
import asyncio
from financial_research_agent.manager_enhanced import EnhancedFinancialResearchManager


def test_progress_callback():
    """Test that progress callback is called correctly."""
    progress_updates = []

    def mock_callback(progress: float, description: str):
        """Capture progress updates."""
        progress_updates.append((progress, description))
        print(f"[{progress:.0%}] {description}")

    # Create manager with callback
    manager = EnhancedFinancialResearchManager(progress_callback=mock_callback)

    # Verify callback is stored
    assert manager.progress_callback is not None, "Callback not stored"

    # Test the _report_progress method directly
    manager._report_progress(0.5, "Test progress update")

    # Verify callback was called
    assert len(progress_updates) == 1, f"Expected 1 update, got {len(progress_updates)}"
    assert progress_updates[0] == (0.5, "Test progress update"), "Callback received wrong data"

    print("\n✅ Progress callback test PASSED")
    print(f"   Captured {len(progress_updates)} progress update(s)")


if __name__ == "__main__":
    test_progress_callback()
