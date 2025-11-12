# Issues & Enhancements Tracker

**Project:** Financial Research Agent
**Last Updated:** 2025-11-11

---

## Active Enhancements

### 🔹 Enhancement #1: Company Metadata File for Robust Name Lookup

**Status:** Proposed
**Priority:** Medium
**Category:** UX Improvement
**Effort:** 1-2 hours

**Description:**
Create a `company_metadata.json` file during analysis generation to store ticker and official company name from SEC EDGAR. This would eliminate the need for regex parsing of comprehensive reports to extract company names.

**Current Limitation:**
The web app currently extracts company names from comprehensive reports using regex patterns. While this works for existing reports, it's fragile and depends on consistent Executive Summary formatting.

**Proposed Solution:**
When the EDGAR agent generates an analysis, create a metadata file at the beginning:

```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "cik": "0000320193",
  "analysis_date": "2025-11-11",
  "fiscal_period": "Q3 2024",
  "generated_at": "2025-11-11T14:35:22Z"
}
```

**Implementation Notes:**
- File location: `financial_research_agent/output/{timestamp}/00_metadata.json`
- Generate during planner agent initialization (has access to SEC EDGAR data)
- Update `web_app.py` dropdown logic to read from metadata file first, fall back to regex
- Use edgartools `Company` class to get official name: `Company(ticker).name`

**Benefits:**
- Reliable company name display in dropdown
- Faster startup (no regex processing)
- Additional metadata available for future features
- Consistent data source (SEC EDGAR)

**Related Files:**
- `financial_research_agent/agents/planner_agent.py` - Add metadata file creation
- `financial_research_agent/web_app.py` (lines 105-127) - Update dropdown logic

**Origin:**
User suggestion during UX improvement session (2025-11-11)

---

## Future Enhancements (Backlog)

### 🔹 Enhancement #2: Dark Mode Toggle

**Status:** Backlog
**Priority:** Low
**Category:** UX Enhancement

**Description:**
Add dark mode theme toggle for the Gradio interface. Popular in financial platforms (Bloomberg Terminal has dark mode).

**Reference:** See `UX_REDESIGN_PROPOSAL.md` Phase 2 enhancements

---

### 🔹 Enhancement #3: Sticky Table Headers

**Status:** Backlog
**Priority:** Low
**Category:** UX Enhancement

**Description:**
Make financial table headers stay visible when scrolling long tables.

**Reference:** See `UX_REDESIGN_PROPOSAL.md` Phase 2 enhancements

---

### 🔹 Enhancement #4: 20-F Support for Australian Companies

**Status:** Planned
**Priority:** High
**Category:** Feature Addition
**Effort:** 2-3 days

**Description:**
Support foreign company filings (20-F forms) for international analysis, specifically Australian companies.

**Reference:** See `MASTER_DEV_PLAN.md` Priority #2

---

## Resolved Issues

### ✅ Issue #1: Dropdown Showing "Comprehensive Report" Instead of Company Names

**Resolved:** 2025-11-11
**Priority:** High
**Category:** Bug

**Description:**
The "View Existing Analysis" dropdown was displaying "Comprehensive Report" as the label instead of company names like "Apple (AAPL)".

**Solution:**
Implemented regex parsing of comprehensive reports to extract company names from Executive Summary first sentence. Patterns match possessives and verbs: "'s", "fiscal", "Q[0-9]", "latest", "reported".

**Files Modified:**
- `financial_research_agent/web_app.py` (lines 105-127)

---

### ✅ Issue #2: Knowledge Base Query Generator Error

**Resolved:** 2025-11-11
**Priority:** High
**Category:** Bug

**Description:**
KB search throwing error: `'generator' object has no attribute 'expandtabs'`

**Root Cause:**
Wrapper function was returning a generator object instead of directly passing it to Gradio.

**Solution:**
Changed button click handler from wrapper function to lambda that directly invokes `query_knowledge_base()`.

**Files Modified:**
- `financial_research_agent/web_app.py` (lines 1573-1577)

---

### ✅ Issue #3: Report Tabs Not Nested Under Parent Tab

**Resolved:** 2025-11-11
**Priority:** Medium
**Category:** UX Improvement

**Description:**
All 6 report tabs (Comprehensive Report, Financial Statements, etc.) were at the top level instead of nested under a "Reports" parent tab.

**Solution:**
Added parent "Reports" tab with nested Tabs() container. Restructured indentation for all 6 child tabs.

**Files Modified:**
- `financial_research_agent/web_app.py` (lines 1334-1503)

---

## Issue Classification Guide

**Priority Levels:**
- **Critical:** Blocking functionality, data loss, security issues
- **High:** Significant user impact, core feature bugs
- **Medium:** Moderate user impact, workarounds available
- **Low:** Minor issues, cosmetic improvements

**Categories:**
- **Bug:** Incorrect behavior, errors, broken functionality
- **Enhancement:** New features, improvements to existing features
- **UX Improvement:** User interface/experience refinements
- **Performance:** Speed, efficiency, resource usage
- **Documentation:** Docs, comments, guides
- **Technical Debt:** Refactoring, code quality

**Status:**
- **Proposed:** Suggested but not yet approved
- **Backlog:** Approved but not yet scheduled
- **Planned:** Scheduled for specific milestone
- **In Progress:** Currently being worked on
- **Resolved:** Completed and verified

---

## How to Add Issues/Enhancements

1. Add new entry under appropriate section (Active/Future/Resolved)
2. Assign unique ID number (sequential within category)
3. Set status, priority, category, and effort estimate
4. Provide clear description with context
5. Include implementation notes if known
6. Reference related files and line numbers
7. Update "Last Updated" date at top of document

---

**Questions or suggestions?** Discuss in project planning sessions or add notes directly to this file.
