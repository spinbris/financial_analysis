# Stock Price Charts - Test Plan

**Feature**: Live Stock Price Charts using yfinance integration
**Date**: 2025-11-12
**Status**: Ready for Testing

---

## Overview

This document outlines the comprehensive test plan for the newly implemented Stock Price Charts feature in the Financial Research Agent web application. The feature provides real-time stock data visualization using Yahoo Finance data.

### Feature Scope
- Fetch live stock price data using yfinance library
- Display interactive Plotly charts with price and volume subplots
- Support multiple time periods (1mo, 3mo, 6mo, 1y, 2y, 5y)
- Calculate and display key statistics
- NOT indexed in Knowledge Base (on-demand data only)
- Located in dedicated "Stock Performance" tab

---

## Test Categories

### 1. Functional Tests

#### 1.1 Valid Ticker Symbol Tests
| Test ID | Test Case | Ticker | Period | Expected Result |
|---------|-----------|--------|--------|----------------|
| F-001 | Large cap US stock | AAPL | 1y | Chart displays with accurate data |
| F-002 | Tech stock | MSFT | 6mo | Chart displays with accurate data |
| F-003 | Different sector | JPM | 1y | Chart displays with accurate data |
| F-004 | High volatility stock | TSLA | 3mo | Chart displays with accurate data |
| F-005 | ETF | SPY | 2y | Chart displays with accurate data |

#### 1.2 Time Period Tests
| Test ID | Test Case | Ticker | Period | Expected Result |
|---------|-----------|--------|--------|----------------|
| F-006 | 1 month period | AAPL | 1mo | Chart shows ~22 trading days |
| F-007 | 3 month period | AAPL | 3mo | Chart shows ~65 trading days |
| F-008 | 6 month period | AAPL | 6mo | Chart shows ~130 trading days |
| F-009 | 1 year period | AAPL | 1y | Chart shows ~252 trading days |
| F-010 | 2 year period | AAPL | 2y | Chart shows ~504 trading days |
| F-011 | 5 year period | AAPL | 5y | Chart shows ~1260 trading days |

#### 1.3 Edge Cases
| Test ID | Test Case | Input | Expected Result |
|---------|-----------|-------|----------------|
| F-012 | Lowercase ticker | aapl | Auto-converted to AAPL, chart displays |
| F-013 | Mixed case ticker | AaPl | Auto-converted to AAPL, chart displays |
| F-014 | Ticker with spaces | " AAPL " | Spaces trimmed, chart displays |
| F-015 | Recently IPO'd stock | Recent IPO | Limited data message or available data |
| F-016 | Delisted stock | Historical delisted ticker | No data found error message |

---

### 2. Error Handling Tests

#### 2.1 Invalid Input Tests
| Test ID | Test Case | Input | Expected Result |
|---------|-----------|-------|----------------|
| E-001 | Empty ticker field | "" | "Please enter a valid ticker symbol" |
| E-002 | Whitespace only | "   " | "Please enter a valid ticker symbol" |
| E-003 | Invalid ticker symbol | INVALID123 | "No data found for ticker" error |
| E-004 | Special characters | @#$% | "No data found for ticker" error |
| E-005 | Very long string | 50+ characters | "No data found for ticker" error |
| E-006 | Numeric only | 12345 | "No data found for ticker" error |

#### 2.2 System Error Tests
| Test ID | Test Case | Scenario | Expected Result |
|---------|-----------|----------|----------------|
| E-007 | Network timeout | Simulate slow connection | Graceful error message |
| E-008 | Yahoo Finance unavailable | API down scenario | "Error fetching data" message |
| E-009 | Rate limiting | Rapid successive requests | Handle gracefully or show limit message |

---

### 3. UI/UX Tests

#### 3.1 Navigation Tests
| Test ID | Test Case | Action | Expected Result |
|---------|-----------|--------|----------------|
| U-001 | Find Stock Performance tab | Locate tab in ribbon | Tab visible with "📈 Stock Performance" label |
| U-002 | Tab accessibility | Click tab | Tab opens, shows intro text and inputs |
| U-003 | Tab position | Check tab order | Located after EDGAR Filings tab |

#### 3.2 Component Interaction Tests
| Test ID | Test Case | Action | Expected Result |
|---------|-----------|--------|----------------|
| U-004 | Ticker input field | Click and type | Text entry works, placeholder visible |
| U-005 | Period dropdown | Click dropdown | Shows all 6 options (1mo, 3mo, 6mo, 1y, 2y, 5y) |
| U-006 | Period selection | Select different period | Selection updates correctly |
| U-007 | Fetch button | Click button | Button responds, shows loading state |
| U-008 | Chart display | After successful fetch | Chart appears, is interactive |
| U-009 | Statistics display | After successful fetch | Stats markdown renders correctly |
| U-010 | Hover on chart | Hover over data points | Tooltip shows date, price, volume |
| U-011 | Zoom on chart | Use Plotly zoom | Chart zooms correctly |
| U-012 | Pan on chart | Use Plotly pan | Chart pans correctly |
| U-013 | Reset chart view | Click reset button | Chart returns to default view |

#### 3.3 Responsiveness Tests
| Test ID | Test Case | Action | Expected Result |
|---------|-----------|--------|----------------|
| U-014 | Window resize | Resize browser window | Chart resizes appropriately |
| U-015 | Mobile view | View on mobile device | Layout remains usable |
| U-016 | Large screen | View on large monitor | Chart scales up appropriately |

---

### 4. Data Validation Tests

#### 4.1 Data Accuracy Tests
| Test ID | Test Case | Validation Point | Expected Result |
|---------|-----------|------------------|----------------|
| D-001 | Current price | Compare with Yahoo Finance | Matches within $0.01 |
| D-002 | Price change % | Verify calculation | Accurate calculation |
| D-003 | 52-week high | Compare with Yahoo Finance | Matches actual high |
| D-004 | 52-week low | Compare with Yahoo Finance | Matches actual low |
| D-005 | Average volume | Verify calculation | Reasonable average |
| D-006 | Last updated date | Check date stamp | Shows most recent trading day |

#### 4.2 Chart Data Tests
| Test ID | Test Case | Validation Point | Expected Result |
|---------|-----------|------------------|----------------|
| D-007 | Price line continuity | Visual inspection | No gaps on trading days |
| D-008 | Volume bars alignment | Check x-axis alignment | Volume matches price dates |
| D-009 | Weekend/holiday gaps | Check date continuity | Gaps on non-trading days |
| D-010 | Historical accuracy | Compare 1-year ago price | Matches historical records |

---

### 5. Integration Tests

#### 5.1 Component Integration
| Test ID | Test Case | Action | Expected Result |
|---------|-----------|--------|----------------|
| I-001 | Full workflow | Enter ticker → select period → fetch | Complete flow works end-to-end |
| I-002 | Multiple fetches | Fetch different tickers sequentially | Each fetch updates correctly |
| I-003 | Period change | Fetch → change period → fetch again | New period data loads |
| I-004 | Tab switching | Fetch chart → switch tabs → return | Chart persists correctly |
| I-005 | Other tabs unaffected | Use stock charts | Other tabs continue to work |

#### 5.2 Dependency Integration
| Test ID | Test Case | Check | Expected Result |
|---------|-----------|-------|----------------|
| I-006 | yfinance library | Import and use | No import errors |
| I-007 | Plotly library | Chart rendering | Charts render correctly |
| I-008 | Python environment | Check .venv | Correct dependencies installed |

---

### 6. Performance Tests

#### 6.1 Speed Tests
| Test ID | Test Case | Action | Acceptable Time |
|---------|-----------|--------|----------------|
| P-001 | 1 month data fetch | Fetch 1mo data | < 3 seconds |
| P-002 | 1 year data fetch | Fetch 1y data | < 5 seconds |
| P-003 | 5 year data fetch | Fetch 5y data | < 8 seconds |
| P-004 | Chart rendering | Display chart | < 1 second |

#### 6.2 Resource Tests
| Test ID | Test Case | Action | Expected Result |
|---------|-----------|--------|----------------|
| P-005 | Memory usage | Fetch multiple charts | No memory leaks |
| P-006 | Multiple concurrent users | 5+ simultaneous fetches | All complete successfully |
| P-007 | Repeated fetches | 10 consecutive fetches | Performance remains consistent |

---

## Test Execution Matrix

### Priority Test Combinations
Test these ticker/period combinations thoroughly:

| Priority | Ticker | Period | Rationale |
|----------|--------|--------|-----------|
| HIGH | AAPL | 1y | Most common use case |
| HIGH | MSFT | 6mo | Popular tech stock |
| HIGH | SPY | 1y | Market index ETF |
| MEDIUM | TSLA | 3mo | High volatility |
| MEDIUM | JPM | 2y | Financial sector |
| MEDIUM | GOOGL | 1y | Different company structure |
| LOW | NVDA | 5y | Long-term view |
| LOW | AMZN | 1mo | Short-term view |

---

## Acceptance Criteria

The feature passes testing if:

### Must Have (Blockers)
- ✅ Valid ticker symbols display charts correctly
- ✅ All 6 time periods work correctly
- ✅ Invalid tickers show user-friendly error messages
- ✅ Empty input is handled gracefully
- ✅ Statistics calculations are accurate
- ✅ Charts are interactive (zoom, pan, hover)
- ✅ No crashes or unhandled exceptions

### Should Have (Important)
- ✅ Charts render in < 5 seconds for 1-year data
- ✅ Error messages are clear and actionable
- ✅ UI is intuitive and matches app design
- ✅ Tab navigation works smoothly
- ✅ Data matches Yahoo Finance source
- ✅ Charts are professionally styled

### Nice to Have (Enhancements)
- Mobile responsiveness
- Keyboard navigation support
- Chart export functionality
- Multiple ticker comparison (future feature)

---

## Manual Testing Script

### Pre-Test Setup
1. Ensure all background processes are killed: `pkill -f "launch_web_app.py"`
2. Verify clean environment: `ps aux | grep launch_web_app | grep -v grep | wc -l` (should be 0)
3. Start web app: `SEC_EDGAR_USER_AGENT="FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)" .venv/bin/python launch_web_app.py`
4. Wait for "Running on local URL" message
5. Open browser to local URL

### Test Execution Steps

#### Test Suite 1: Basic Functionality (15 min)
```
1. Navigate to "📈 Stock Performance" tab
2. Enter "AAPL" in ticker field
3. Select "1y" from period dropdown
4. Click "📊 Fetch Chart" button
5. Verify:
   - Chart appears with price line
   - Volume bars appear below
   - Statistics show current price, change %, 52w high/low, avg volume
   - Last updated date is recent
   - Chart is interactive (try zoom/pan)

6. Change period to "3mo"
7. Click fetch again
8. Verify chart updates with 3-month data

9. Enter "MSFT"
10. Click fetch
11. Verify Microsoft data displays correctly

12. Enter "INVALID123"
13. Click fetch
14. Verify error message: "No data found for ticker"

15. Clear ticker field
16. Click fetch
17. Verify error message: "Please enter a valid ticker symbol"
```

#### Test Suite 2: Edge Cases (10 min)
```
1. Enter "aapl" (lowercase)
2. Verify auto-converts to AAPL and works

3. Enter " AAPL " (with spaces)
4. Verify spaces are trimmed and works

5. Enter "SPY" (ETF)
6. Verify ETF data displays correctly

7. Enter "TSLA"
8. Select "5y"
9. Verify 5-year historical data loads

10. Enter "@#$%"
11. Verify error handling
```

#### Test Suite 3: UI/UX (10 min)
```
1. Test all period options in dropdown
2. Verify each period displays correct date range

3. Hover over chart data points
4. Verify tooltips show correct information

5. Use Plotly zoom tools
6. Verify zoom works correctly

7. Use Plotly pan tools
8. Verify pan works correctly

9. Click reset axes button
10. Verify chart returns to default view

11. Switch to different tab
12. Switch back to Stock Performance
13. Verify chart persists

14. Resize browser window
15. Verify chart resizes appropriately
```

#### Test Suite 4: Data Validation (5 min)
```
1. Fetch AAPL 1y data
2. Open Yahoo Finance in another tab
3. Compare:
   - Current price (within $0.01)
   - 52-week high
   - 52-week low
   - Recent price trend
4. Verify data accuracy
```

---

## Test Results Template

### Test Session Information
- **Date**: _______________
- **Tester**: _______________
- **App Version**: 0.1.0
- **Environment**: Local development

### Results Summary
- **Total Tests Executed**: _____ / _____
- **Passed**: _____
- **Failed**: _____
- **Blocked**: _____
- **Skipped**: _____

### Failed Tests
| Test ID | Description | Actual Result | Severity | Notes |
|---------|-------------|---------------|----------|-------|
|         |             |               |          |       |

### Bugs Found
| Bug ID | Severity | Description | Steps to Reproduce | Expected | Actual |
|--------|----------|-------------|-------------------|----------|--------|
|        |          |             |                   |          |        |

### Sign-off
- [ ] All HIGH priority tests passed
- [ ] All blocking bugs resolved
- [ ] Feature ready for production

**Tester Signature**: _______________
**Date**: _______________

---

## Notes

- Tests should be executed in the order presented
- Document any unexpected behavior immediately
- Screenshots encouraged for UI issues
- Performance times may vary based on network conditions
- yfinance data is subject to Yahoo Finance availability
- Some tickers may have limited historical data
- Market hours may affect real-time data accuracy

---

## References

- Implementation file: [web_app.py](financial_research_agent/web_app.py)
- Test script: [test_stock_chart.py](test_stock_chart.py)
- Dependencies: [pyproject.toml](pyproject.toml)
- yfinance documentation: https://pypi.org/project/yfinance/
- Plotly documentation: https://plotly.com/python/
