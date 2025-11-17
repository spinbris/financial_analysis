# Development Workflow Guide

## Quick Start

### Local Development Setup

#### 1. Backend (Python + Gradio)

```bash
cd /Users/stephenparton/projects/financial_analysis

# Activate virtual environment
source .venv/bin/activate

# Set environment variable
export SEC_EDGAR_USER_AGENT="FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)"

# Start Gradio interface
python launch_web_app.py
```

**Access**: http://localhost:7860

**Use for**:
- Generating new analyses
- Viewing existing analyses
- Running KB queries locally

#### 2. Frontend (React + TypeScript)

```bash
cd /Users/stephenparton/projects/Gradioappfrontend

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
```

**Access**: http://localhost:5173

**Use for**:
- UI/UX enhancements
- Testing visualizations
- Source attribution display
- Chart generation

#### 3. Local API Bridge (Optional)

For connecting React frontend to local ChromaDB:

```bash
cd /Users/stephenparton/projects/financial_analysis

# Run local FastAPI bridge
python -m financial_research_agent.modal.modal_fastapi_bridge_local
```

**Access**: http://localhost:8000

**Endpoints**:
- `/api/health` - Health check
- `/api/query` - RAG queries
- `/api/companies` - List indexed companies

## Common Tasks

### Generate New Analysis

```bash
cd /Users/stephenparton/projects/financial_analysis

# Interactive (Gradio)
python launch_web_app.py

# Or command-line
echo "Comprehensive financial analysis of <COMPANY>" | \
  SEC_EDGAR_USER_AGENT="FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)" \
  .venv/bin/python -m financial_research_agent.main_enhanced \
  --ticker <TICKER> \
  --mode full
```

**Output**: `./financial_research_agent/output/<timestamp>/`

### Index Analysis to ChromaDB

```bash
# Check current KB status
python -c "
from financial_research_agent.rag.chroma_manager import FinancialRAGManager
rag = FinancialRAGManager(persist_directory='./chroma_db')
print(f'Companies indexed: {rag.collection.count()}')
print(rag.get_companies_with_status())
"

# Re-index specific company (uses upsert - safe for duplicates)
python -c "
from financial_research_agent.rag.chroma_manager import FinancialRAGManager
from pathlib import Path

rag = FinancialRAGManager(persist_directory='./chroma_db')
analysis_dir = Path('./financial_research_agent/output/<timestamp>')
result = rag.index_analysis_from_directory(analysis_dir, '<TICKER>')
print(result)
"
```

### Sync to Modal (Production)

```bash
cd /Users/stephenparton/projects/financial_analysis

# Upload local ChromaDB to Modal volume
python scripts/sync_chromadb_to_modal.py

# Deploy FastAPI bridge
modal deploy financial_research_agent/modal/modal_fastapi_bridge.py
```

### Build and Deploy React Frontend

```bash
cd /Users/stephenparton/projects/Gradioappfrontend

# Build production bundle
npm run build

# Output: ./dist/ directory

# Copy build to Modal deployment (done automatically by modal_fastapi_bridge.py)
```

## Source Attribution Workflow

### For Core SEC Analyses (Current)

All existing analyses automatically get tagged as:
- `source_tier: "core"`
- `data_source: "SEC-10K"` or `"SEC-10Q"`
- `validation_status: "validated"`
- `enhancement_type: "none"`

**No changes needed** - this happens automatically when indexing.

### For Enhanced Visualizations (Future)

When you add charts/graphs:

1. **Generate chart from validated data**:
   ```python
   # Example: Generate profit margin chart from core analysis
   from financial_research_agent.enhancements import generate_chart

   chart_data = generate_chart(
       ticker="AAPL",
       chart_type="profit_margins",
       data_source="core_analysis"  # Must come from validated SEC data
   )
   ```

2. **Index with enhanced metadata**:
   ```python
   rag.collection.add(
       documents=[chart_description],
       metadatas=[{
           "ticker": "AAPL",
           "source_tier": "enhanced",
           "data_source": "SEC-10K",
           "validation_status": "validated",
           "enhancement_type": "chart",
           "chart_type": "profit_margins"
       }],
       ids=[f"AAPL_enhanced_chart_margins"]
   )
   ```

### For Supplemental Web Context (Future)

When adding web search results:

```python
rag.collection.add(
    documents=[web_search_result],
    metadatas=[{
        "ticker": "AAPL",
        "source_tier": "supplemental",
        "data_source": "web-search",
        "validation_status": "unverified",
        "enhancement_type": "web-context",
        "search_query": "Apple recent news"
    }],
    ids=[f"AAPL_supplemental_web_<timestamp>"]
)
```

## React Component Usage

### Display Source Badges

```tsx
import { SourceBadge, SourceBadgeGroup, SourceLegend } from './components/SourceBadge';

// Single badge
<SourceBadge
  sourceTier="core"
  dataSource="SEC-10K"
  validationStatus="validated"
/>

// Multiple sources
<SourceBadgeGroup
  sources={[
    { sourceTier: 'core', dataSource: 'SEC-10K' },
    { sourceTier: 'enhanced', dataSource: 'SEC-10K' }
  ]}
/>

// Show legend
<SourceLegend />
```

### In Query Results

```tsx
function QueryResult({ result }) {
  return (
    <div className="result-card">
      <div className="result-header">
        <SourceBadge
          sourceTier={result.metadata.source_tier}
          dataSource={result.metadata.data_source}
          validationStatus={result.metadata.validation_status}
        />
      </div>
      <div className="result-content">
        {result.content}
      </div>
    </div>
  );
}
```

## Testing

### Test ChromaDB Metadata

```python
# Check that source attribution is working
from financial_research_agent.rag.chroma_manager import FinancialRAGManager

rag = FinancialRAGManager(persist_directory='./chroma_db')

# Query and check metadata
results = rag.query(
    query_text="What are Apple's revenue sources?",
    ticker="AAPL",
    n_results=3
)

for i, result in enumerate(results['metadatas'][0]):
    print(f"\nResult {i+1}:")
    print(f"  Source Tier: {result.get('source_tier', 'N/A')}")
    print(f"  Data Source: {result.get('data_source', 'N/A')}")
    print(f"  Validation: {result.get('validation_status', 'N/A')}")
    print(f"  Enhancement: {result.get('enhancement_type', 'N/A')}")
```

### Test React Components

```bash
cd /Users/stephenparton/projects/Gradioappfrontend

# Start dev server
npm run dev

# Open http://localhost:5173 and test:
# - Source badges render correctly
# - Colors and icons display properly
# - Hover tooltips work
# - Legend is readable
```

## Git Workflow

### Backend Repository

```bash
cd /Users/stephenparton/projects/financial_analysis

git status
git add financial_research_agent/rag/chroma_manager.py
git add ARCHITECTURE.md DEV_WORKFLOW.md
git commit -m "feat: add source attribution metadata system"
git push origin main
```

### Frontend Repository

```bash
cd /Users/stephenparton/projects/Gradioappfrontend

git status
git add src/components/SourceBadge.tsx
git commit -m "feat: add source attribution badge components"
git push origin main
```

## Troubleshooting

### ChromaDB Issues

```bash
# Reset local ChromaDB (⚠️ deletes all data)
rm -rf ./chroma_db

# Re-index all companies
python scripts/reindex_all_companies.py
```

### React Build Issues

```bash
cd /Users/stephenparton/projects/Gradioappfrontend

# Clear cache and reinstall
rm -rf node_modules dist .vite
npm install
npm run dev
```

### Modal Deployment Issues

```bash
# Check Modal status
modal app list

# View logs
modal app logs <app-name>

# Force redeploy
modal deploy --force financial_research_agent/modal/modal_fastapi_bridge.py
```

### Port Conflicts

```bash
# Kill process on port 7860 (Gradio)
lsof -ti:7860 | xargs kill -9

# Kill process on port 5173 (React)
lsof -ti:5173 | xargs kill -9

# Kill process on port 8000 (FastAPI)
lsof -ti:8000 | xargs kill -9
```

## Environment Variables

### Required

```bash
# Backend
export SEC_EDGAR_USER_AGENT="FinancialResearchAgent/1.0 (your-email@example.com)"
export OPENAI_API_KEY="sk-..."

# Frontend (optional, for connecting to local API)
# Create .env.development in Gradioappfrontend/
VITE_API_URL=http://localhost:8000
```

### Optional

```bash
# Use Groq instead of OpenAI
export GROQ_API_KEY="gsk_..."
export LLM_PROVIDER="groq"
export OPENAI_BASE_URL="https://api.groq.com/openai/v1"
```

## Key Files Reference

### Backend
- `financial_research_agent/main_enhanced.py` - Main orchestrator
- `financial_research_agent/rag/chroma_manager.py` - ChromaDB operations
- `financial_research_agent/rag/intelligence.py` - RAG query logic
- `financial_research_agent/web_app.py` - Gradio interface
- `financial_research_agent/modal/modal_fastapi_bridge.py` - Production API
- `scripts/sync_chromadb_to_modal.py` - Data sync utility

### Frontend
- `src/App.tsx` - Main React app
- `src/components/SourceBadge.tsx` - Source attribution badges
- `src/components/QueryInterface.tsx` - Query UI (to be updated)
- `src/api/client.ts` - API client

## Next Steps

1. ✅ **Set up local React development** - Complete
2. ✅ **Add source attribution metadata** - Complete
3. ✅ **Create SourceBadge component** - Complete
4. ⏳ **Update RAG query response** - Include metadata in results
5. ⏳ **Integrate SourceBadge into query results** - Display badges in React UI
6. ⏳ **Test end-to-end** - Verify badges show correctly for different source tiers
7. ⏳ **Deploy to Modal** - Sync and deploy enhanced system

## Resources

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [React Hooks](https://react.dev/reference/react)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Modal Documentation](https://modal.com/docs)
- [SEC EDGAR API](https://www.sec.gov/edgar/sec-api-documentation)
