# Database Integration Guide

## Overview

Currently, the Financial Research Agent saves reports as markdown files in timestamped directories. For production use or enhanced features, consider database integration.

## Should You Use a Database?

### Reasons to Add a Database

✅ **Query History** - Track what analyses have been run
✅ **Report Caching** - Avoid re-running expensive analyses
✅ **Search & Discovery** - Find previous reports quickly
✅ **Multi-User Support** - Share analyses across team
✅ **Trending Analysis** - Track how metrics change over time
✅ **API Integration** - Enable programmatic access
✅ **Report Versioning** - Track changes in analyses
✅ **User Preferences** - Remember settings per user

### Reasons to Skip Database (For Now)

❌ **Single User** - Just you using it locally
❌ **Low Volume** - Only occasional analyses
❌ **File-Based Works** - Current markdown files meet needs
❌ **Simplicity** - Don't want to manage a database
❌ **Quick Prototyping** - Still exploring what to build

## Database Options

### Option 1: SQLite (Recommended for Starting)

**Best For:** Single user, embedded solution, simple setup

**Pros:**
- Zero configuration
- No separate server needed
- Built into Python
- Perfect for local desktop app
- Easy to backup (single file)

**Cons:**
- Single writer at a time
- Not ideal for concurrent web users
- Limited scaling

**Schema Example:**

```sql
-- Sessions table
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    query TEXT NOT NULL,
    company_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT, -- 'running', 'completed', 'failed'
    duration_seconds INTEGER
);

-- Reports table
CREATE TABLE reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT REFERENCES sessions(session_id),
    report_type TEXT NOT NULL, -- 'comprehensive', 'statements', 'metrics', 'verification'
    content TEXT NOT NULL,
    format TEXT DEFAULT 'markdown',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Financial data table (for caching)
CREATE TABLE financial_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_cik TEXT NOT NULL,
    company_name TEXT,
    filing_type TEXT, -- '10-Q', '10-K'
    filing_date DATE,
    period_end_date DATE,
    data_json TEXT, -- JSON blob of statements
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_cik, filing_type, period_end_date)
);

-- Metrics cache
CREATE TABLE metrics_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_cik TEXT NOT NULL,
    period_end_date DATE NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_cik, period_end_date, metric_name)
);

-- Full-text search index
CREATE VIRTUAL TABLE reports_fts USING fts5(
    session_id UNINDEXED,
    report_type UNINDEXED,
    content,
    tokenize='porter unicode61'
);
```

**Implementation:**

```python
# financial_research_agent/database.py
import sqlite3
import json
from datetime import datetime
from pathlib import Path

class ReportsDatabase:
    def __init__(self, db_path: str = "financial_reports.db"):
        self.db_path = db_path
        self.conn = None
        self._init_db()

    def _init_db(self):
        """Initialize database with schema."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

        # Create tables (use schema above)
        self.conn.executescript("""
            -- Insert schema SQL here
        """)
        self.conn.commit()

    def save_session(self, session_id: str, query: str, company_name: str = None):
        """Save a new analysis session."""
        self.conn.execute("""
            INSERT INTO sessions (session_id, query, company_name, status)
            VALUES (?, ?, ?, 'running')
        """, (session_id, query, company_name))
        self.conn.commit()

    def save_report(self, session_id: str, report_type: str, content: str):
        """Save a generated report."""
        self.conn.execute("""
            INSERT INTO reports (session_id, report_type, content)
            VALUES (?, ?, ?)
        """, (session_id, report_type, content))

        # Also add to FTS index
        self.conn.execute("""
            INSERT INTO reports_fts (session_id, report_type, content)
            VALUES (?, ?, ?)
        """, (session_id, report_type, content))

        self.conn.commit()

    def get_session_reports(self, session_id: str) -> dict:
        """Retrieve all reports for a session."""
        cursor = self.conn.execute("""
            SELECT report_type, content
            FROM reports
            WHERE session_id = ?
        """, (session_id,))

        return {row['report_type']: row['content'] for row in cursor}

    def search_reports(self, query: str, limit: int = 10):
        """Full-text search across all reports."""
        cursor = self.conn.execute("""
            SELECT
                r.session_id,
                s.query,
                s.company_name,
                r.report_type,
                snippet(reports_fts, -1, '<mark>', '</mark>', '...', 50) as snippet,
                rank
            FROM reports_fts r
            JOIN sessions s ON r.session_id = s.session_id
            WHERE reports_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))

        return [dict(row) for row in cursor]

    def cache_financial_data(self, company_cik: str, filing_type: str,
                           period_end_date: str, data: dict):
        """Cache extracted financial data."""
        self.conn.execute("""
            INSERT OR REPLACE INTO financial_data
            (company_cik, filing_type, period_end_date, data_json)
            VALUES (?, ?, ?, ?)
        """, (company_cik, filing_type, period_end_date, json.dumps(data)))
        self.conn.commit()

    def get_cached_data(self, company_cik: str, filing_type: str,
                       period_end_date: str) -> dict | None:
        """Retrieve cached financial data."""
        cursor = self.conn.execute("""
            SELECT data_json
            FROM financial_data
            WHERE company_cik = ?
              AND filing_type = ?
              AND period_end_date = ?
              AND extracted_at > datetime('now', '-7 days')
        """, (company_cik, filing_type, period_end_date))

        row = cursor.fetchone()
        return json.loads(row['data_json']) if row else None
```

### Option 2: PostgreSQL (Production-Grade)

**Best For:** Multi-user web app, high volume, team collaboration

**Pros:**
- Excellent concurrency
- JSONB for flexible schema
- Full-text search built-in
- Scales to millions of records
- Battle-tested reliability

**Cons:**
- Requires separate server
- More complex setup
- Overkill for single user

**When to Use:**
- Deploying as web service with multiple users
- Need advanced analytics and reporting
- Want to integrate with other enterprise systems
- Building a SaaS product

### Option 3: DuckDB (Analytics-Focused)

**Best For:** Analytical queries, time-series analysis, data science workflows

**Pros:**
- Extremely fast analytics
- Excellent with large datasets
- Parquet file support
- SQL interface familiar to analysts
- Can query CSV/Parquet directly

**Cons:**
- Newer, less mature ecosystem
- Primarily analytical, not transactional
- Not ideal for real-time writes

**When to Use:**
- Analyzing trends across many reports
- Building data science pipelines
- Creating aggregated metrics dashboards
- Running complex analytical queries

### Option 4: Vector Database (Semantic Search)

**Best For:** Semantic search, RAG applications, finding similar analyses

**Options:**
- **ChromaDB** - Embedded, easy to use
- **Pinecone** - Managed service
- **Weaviate** - Self-hosted, feature-rich

**Example Use Cases:**
- "Find analyses similar to this one"
- "Which companies have declining ROE trends?"
- "Show me all risk assessments mentioning supply chain"
- RAG-powered Q&A over historical reports

**Schema Example (ChromaDB):**

```python
import chromadb
from chromadb.config import Settings

class ReportsVectorDB:
    def __init__(self):
        self.client = chromadb.Client(Settings(
            persist_directory="./chroma_db"
        ))
        self.collection = self.client.get_or_create_collection(
            name="financial_reports",
            metadata={"hnsw:space": "cosine"}
        )

    def add_report(self, session_id: str, report_type: str,
                  content: str, metadata: dict):
        """Add report to vector database."""
        self.collection.add(
            documents=[content],
            metadatas=[{
                'session_id': session_id,
                'report_type': report_type,
                **metadata
            }],
            ids=[f"{session_id}_{report_type}"]
        )

    def semantic_search(self, query: str, n_results: int = 5):
        """Semantic search across reports."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results

    def find_similar_companies(self, company_name: str):
        """Find companies with similar financial profiles."""
        # Query with company analysis as the search term
        return self.semantic_search(
            f"financial analysis of {company_name}",
            n_results=5
        )
```

## Hybrid Approach (Recommended)

**Best of both worlds:**

1. **SQLite** - Store structured data (sessions, metadata, metrics)
2. **File System** - Keep markdown reports (easy to read/edit)
3. **ChromaDB** - Add semantic search capabilities (optional)

```python
class HybridStorage:
    def __init__(self):
        self.db = ReportsDatabase()  # SQLite
        self.reports_dir = Path("financial_research_agent/output")
        self.vector_db = ReportsVectorDB()  # Optional

    def save_analysis(self, session_id: str, query: str, reports: dict):
        # 1. Save to SQLite (metadata, metrics)
        self.db.save_session(session_id, query)

        # 2. Save to filesystem (readable markdown)
        session_dir = self.reports_dir / session_id
        session_dir.mkdir(exist_ok=True)
        for report_type, content in reports.items():
            (session_dir / f"{report_type}.md").write_text(content)

        # 3. Save to vector DB (for semantic search)
        for report_type, content in reports.items():
            self.vector_db.add_report(session_id, report_type, content, {
                'query': query,
                'timestamp': datetime.now().isoformat()
            })
```

## Implementation Roadmap

### Phase 1: Add SQLite (Quick Win)
**Effort:** 1-2 days
**Value:** Query history, basic search, report caching

```python
# Add to web_app.py
from financial_research_agent.database import ReportsDatabase

class WebApp:
    def __init__(self):
        self.db = ReportsDatabase()  # Add this
        ...
```

### Phase 2: Implement Caching (Performance)
**Effort:** 2-3 days
**Value:** Avoid re-extracting same company data, faster responses

### Phase 3: Add Search UI (Discovery)
**Effort:** 1 day
**Value:** Users can find past analyses

### Phase 4: Vector Search (Advanced)
**Effort:** 2-3 days
**Value:** Semantic search, find similar companies

## My Recommendation

**For your current use case:**

Start with **hybrid approach (SQLite + filesystem)**:

1. **Keep markdown files** - They're already working well
2. **Add SQLite database** - Track sessions and enable search
3. **Defer vector DB** - Add only if you need semantic search

**When to upgrade:**
- Multi-user deployment → PostgreSQL
- Semantic search needs → Add ChromaDB
- Heavy analytics → Consider DuckDB

## Next Steps

1. ✅ Phase 1 Complete - Web interface with file storage
2. ⏭️ Decide: Do you need database now or later?
3. If now: Start with SQLite hybrid approach
4. If later: Continue with current file-based system

**My suggestion:** Use the web interface for a week with current file-based storage. If you find yourself wanting:
- "What analyses have I run before?"
- "Search across all my reports"
- "Avoid re-analyzing the same company"

Then implement SQLite. Otherwise, files work great!

---

**Questions to consider:**
- How often will you use this? (Daily → database, Occasionally → files OK)
- Will others use it? (Multi-user → PostgreSQL, Solo → SQLite or files)
- Need historical trends? (Yes → database with time-series, No → files OK)
