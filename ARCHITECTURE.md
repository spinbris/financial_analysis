# Financial Research Agent - Architecture

## System Overview

This system uses a **hybrid local + cloud architecture** for financial analysis generation and querying:

```
┌─────────────────────────────────────────────────────────────────┐
│                      LOCAL DEVELOPMENT                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐         ┌──────────────────────┐        │
│  │  Python Backend  │         │   React Frontend     │        │
│  │    (Gradio)      │         │   (localhost:5173)   │        │
│  │                  │         │                      │        │
│  │ • Generate       │         │ • Local testing      │        │
│  │   analyses       │         │ • Enhancement dev    │        │
│  │ • Validate data  │         │ • Chart generation   │        │
│  │ • View reports   │         │ • Source attribution │        │
│  └────────┬─────────┘         └──────────┬───────────┘        │
│           │                              │                     │
│           └──────────┬───────────────────┘                     │
│                      │                                         │
│              ┌───────▼────────┐                               │
│              │  ChromaDB      │                               │
│              │  (./chroma_db) │                               │
│              │                │                               │
│              │ • Local testing│                               │
│              │ • Validation   │                               │
│              └───────┬────────┘                               │
│                      │                                         │
└──────────────────────┼─────────────────────────────────────────┘
                       │
                       │ sync_chromadb_to_modal.py
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PRODUCTION (MODAL CLOUD)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              FastAPI Bridge (Port 8000)                  │  │
│  │                                                          │  │
│  │  • /api/query - RAG queries                            │  │
│  │  • /api/companies - List indexed companies              │  │
│  │  • /api/health - Health check                          │  │
│  │  • Serves React static build                           │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│                  ┌────────▼────────┐                           │
│                  │   ChromaDB      │                           │
│                  │ (Modal Volume)  │                           │
│                  │                 │                           │
│                  │ • Read-only     │                           │
│                  │ • Synced data   │                           │
│                  └─────────────────┘                           │
│                                                                 │
│  Public URL: https://xxx.modal.run                            │
└─────────────────────────────────────────────────────────────────┘
```

## Repository Structure

### Main Backend Repo: `financial_analysis`
- Python agents for SEC analysis generation
- Gradio web interface for local use
- ChromaDB for vector storage
- Modal deployment scripts
- Sync utilities

**Location**: `/Users/stephenparton/projects/financial_analysis`

**Git**: (your main git repo)

### React Frontend Repo: `Gradioappfrontend`
- React/TypeScript UI
- Recharts for visualizations
- Enhanced markdown rendering
- Source attribution components

**Location**: `/Users/stephenparton/projects/Gradioappfrontend`

**Git**: `https://github.com/spinbris/Gradioappfrontend.git`

## Data Flow

### 1. Analysis Generation (Local)

```
User Query → Python Agents → SEC EDGAR API
                ↓
        Raw Financial Data
                ↓
        Validation & Formatting
                ↓
        Markdown Reports (./output/)
                ↓
        ChromaDB Indexing (./chroma_db)
```

**Tools**:
- `python -m financial_research_agent.main_enhanced`
- `python launch_web_app.py` (Gradio interface)

### 2. Enhancement Layer (Local)

```
Core Analysis (validated) → Chart Generation → Enhanced Metadata
                                                      ↓
                                              ChromaDB with source tags
```

**Metadata Structure**:
```python
{
    "source_tier": "core" | "enhanced" | "supplemental",
    "data_source": "SEC-10K" | "SEC-10Q" | "web-search",
    "validation_status": "validated" | "unverified",
    "enhancement_type": "chart" | "graph" | "summary" | "web-context"
}
```

### 3. Production Query (Modal)

```
User Query → FastAPI → ChromaDB (Modal) → RAG Response
                                              ↓
                                    React UI with source badges
```

**Source Badges**:
- 📊 **SEC Verified** - Core analysis from filings
- 📈 **Enhanced Viz** - Charts from validated data
- 🌐 **Web Context** - Supplemental web search

## Development Workflow

### For New Analysis Generation

```bash
# 1. Generate analysis locally (Gradio)
cd /Users/stephenparton/projects/financial_analysis
python launch_web_app.py

# 2. Review and validate in browser
# → http://localhost:7860

# 3. Check ChromaDB indexed properly
python -c "
from financial_research_agent.rag.chroma_manager import FinancialRAGManager
rag = FinancialRAGManager(persist_directory='./chroma_db')
print(f'Total documents: {rag.collection.count()}')
"
```

### For UI Enhancements (React)

```bash
# 1. Start React dev server
cd /Users/stephenparton/projects/Gradioappfrontend
npm run dev

# 2. Connect to local backend
# Set API endpoint in .env.development:
# VITE_API_URL=http://localhost:8000

# 3. Test with local ChromaDB data
cd /Users/stephenparton/projects/financial_analysis
python -m financial_research_agent.modal.modal_fastapi_bridge_local

# 4. View in browser
# → http://localhost:5173
```

### For Production Deployment

```bash
# 1. Generate and validate all analyses locally
# 2. Sync ChromaDB to Modal
python scripts/sync_chromadb_to_modal.py

# 3. Build React frontend
cd /Users/stephenparton/projects/Gradioappfrontend
npm run build

# 4. Deploy to Modal
cd /Users/stephenparton/projects/financial_analysis
modal deploy financial_research_agent/modal/modal_fastapi_bridge.py

# 5. Access public URL
# → https://xxx.modal.run
```

## Source Attribution System

### Tier 1: Core SEC Analysis
- Generated from SEC filings only
- Fully validated and authoritative
- Tagged as `source_tier: "core"`
- Badge: 📊 **SEC Verified**

### Tier 2: Enhanced Visualizations
- Charts/graphs generated from validated data
- No additional external data
- Tagged as `source_tier: "enhanced"`
- Badge: 📈 **Enhanced Viz**

### Tier 3: Supplemental Context
- Web search results (optional)
- Clearly marked as unverified
- Tagged as `source_tier: "supplemental"`
- Badge: 🌐 **Web Context**

## Key Files

### Backend (financial_analysis)
- `financial_research_agent/main_enhanced.py` - Main analysis orchestrator
- `financial_research_agent/web_app.py` - Gradio interface
- `financial_research_agent/rag/chroma_manager.py` - ChromaDB operations
- `financial_research_agent/modal/modal_fastapi_bridge.py` - Production API
- `scripts/sync_chromadb_to_modal.py` - Data sync utility

### Frontend (Gradioappfrontend)
- `src/App.tsx` - Main React application
- `src/components/QueryInterface.tsx` - Query UI component
- `src/components/SourceBadge.tsx` - Source attribution (TO BE CREATED)
- `src/api/client.ts` - API client

## Environment Variables

### Local Development
```bash
# Backend (.env)
SEC_EDGAR_USER_AGENT="FinancialResearchAgent/1.0 (your-email@example.com)"
OPENAI_API_KEY="sk-..."

# Frontend (.env.development)
VITE_API_URL=http://localhost:8000
```

### Production (Modal)
```bash
# Set as Modal secrets
OPENAI_API_KEY="sk-..."
MODAL_API_KEY="ak-..."
```

## Port Assignments

- **7860**: Gradio web interface (local)
- **5173**: React dev server (local)
- **8000**: FastAPI bridge (local & Modal)

## Backup & Version Control

### Backup Strategy
```bash
# Analyses
./financial_research_agent/output/*  # All generated reports

# ChromaDB
./chroma_db/  # Vector database (local)
# Modal volume: automatically backed up by Modal

# Configuration
./financial_research_agent/config.py
.env (gitignored - backup separately)
```

### Git Workflow
```bash
# Backend repo
git add .
git commit -m "feat: add source attribution"
git push origin main

# Frontend repo
cd /Users/stephenparton/projects/Gradioappfrontend
git add .
git commit -m "feat: add source badges"
git push origin main
```

## Future Enhancements

1. **Real-time Sync**: WebSocket connection between local and Modal
2. **Automated Testing**: E2E tests for analysis generation
3. **A/B Testing**: Compare visualization approaches
4. **Performance Monitoring**: Track query latency and accuracy
5. **Multi-user Support**: Session management in React UI

## Troubleshooting

### ChromaDB Sync Issues
```bash
# Check local ChromaDB
python -c "
from financial_research_agent.rag.chroma_manager import FinancialRAGManager
rag = FinancialRAGManager(persist_directory='./chroma_db')
print(rag.get_companies_with_status())
"

# Re-sync to Modal
python scripts/sync_chromadb_to_modal.py
```

### React Build Issues
```bash
cd /Users/stephenparton/projects/Gradioappfrontend
rm -rf node_modules dist
npm install
npm run build
```

### Modal Deployment Issues
```bash
# Check Modal status
modal app list

# View logs
modal app logs <app-name>

# Re-deploy
modal deploy --force financial_research_agent/modal/modal_fastapi_bridge.py
```
