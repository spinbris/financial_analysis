# Quick Start Guide

## 🚀 Start Local Development (3 Commands)

### 1. Start Python Backend (Gradio)
```bash
cd /Users/stephenparton/projects/financial_analysis
export SEC_EDGAR_USER_AGENT="FinancialResearchAgent/1.0 (stephen.parton@sjpconsulting.com)"
python launch_web_app.py
```
**Access**: http://localhost:7860

### 2. Start React Frontend
```bash
cd /Users/stephenparton/projects/Gradioappfrontend
npm run dev
```
**Access**: http://localhost:5173

### 3. Start API Bridge (Optional)
```bash
cd /Users/stephenparton/projects/financial_analysis
python -m financial_research_agent.modal.modal_fastapi_bridge_local
```
**Access**: http://localhost:8000

---

## 📁 Key Files

### Documentation
- [README.md](./README.md) - Project overview
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture
- [DEV_WORKFLOW.md](./DEV_WORKFLOW.md) - Development guide
- [UX_ENHANCEMENT_PLAN.md](./UX_ENHANCEMENT_PLAN.md) - Enhancement roadmap

### Backend
- `financial_research_agent/main_enhanced.py` - Analysis orchestrator
- `financial_research_agent/web_app.py` - Gradio interface
- `financial_research_agent/rag/chroma_manager.py` - ChromaDB + source attribution

### Frontend
- `src/components/SourceBadge.tsx` - Source attribution badges (NEW)
- `src/App.tsx` - Main React app

---

## 🎯 Common Tasks

### Generate New Analysis
```bash
cd /Users/stephenparton/projects/financial_analysis
python launch_web_app.py
# Then use browser at http://localhost:7860
```

### Check ChromaDB Status
```python
python -c "
from financial_research_agent.rag.chroma_manager import FinancialRAGManager
rag = FinancialRAGManager(persist_directory='./chroma_db')
print(f'Companies: {rag.collection.count()}')
print(rag.get_companies_with_status())
"
```

### Sync to Modal
```bash
python scripts/sync_chromadb_to_modal.py
modal deploy financial_research_agent/modal/modal_fastapi_bridge.py
```

---

## 🔧 Troubleshooting

### Port Already in Use
```bash
# Kill Gradio (7860)
lsof -ti:7860 | xargs kill -9

# Kill React (5173)
lsof -ti:5173 | xargs kill -9

# Kill FastAPI (8000)
lsof -ti:8000 | xargs kill -9
```

### Reset ChromaDB
```bash
rm -rf ./chroma_db
# Then re-index companies
```

---

## 📊 Source Attribution System

### Three Badge Types

1. **📊 SEC Verified** - Core analysis from official SEC filings
2. **📈 Enhanced Viz** - Charts from validated data
3. **🌐 Web Context** - Supplemental web search (optional)

### Implementation Status

✅ **Completed**:
- ChromaDB metadata schema updated
- React SourceBadge component created
- Architecture documented

⏳ **Next Steps**:
- Update RAG query response to include metadata
- Integrate badges into React query results
- Add chart generation pipeline

---

## 📚 Repository Structure

```
financial_analysis/                 (Main backend repo)
├── financial_research_agent/
│   ├── agents/                     (Specialist agents)
│   ├── rag/
│   │   ├── chroma_manager.py       ← Source attribution
│   │   └── intelligence.py
│   ├── modal/
│   │   └── modal_fastapi_bridge.py
│   └── output/                     (Generated analyses)
├── scripts/
│   └── sync_chromadb_to_modal.py
├── chroma_db/                      (Local vector DB)
└── *.md                            (Documentation)

Gradioappfrontend/                  (React frontend repo)
├── src/
│   ├── components/
│   │   └── SourceBadge.tsx         ← NEW
│   ├── api/
│   └── App.tsx
└── package.json
```

---

## 🌐 URLs

- **Local Gradio**: http://localhost:7860
- **Local React**: http://localhost:5173
- **Local API**: http://localhost:8000
- **Production**: https://[your-modal-app].modal.run
- **Figma Design**: https://www.figma.com/design/9S86SOBRBmZ5OZRMjGyWBp/Gradio-App-Frontend

---

## 🔑 Environment Variables

```bash
# Required
export SEC_EDGAR_USER_AGENT="FinancialResearchAgent/1.0 (your-email@example.com)"
export OPENAI_API_KEY="sk-..."

# Optional (for Groq)
export GROQ_API_KEY="gsk_..."
export LLM_PROVIDER="groq"
export OPENAI_BASE_URL="https://api.groq.com/openai/v1"
```

---

## 📝 Next Development Steps

1. Update `intelligence.py` to include source metadata in query responses
2. Update Modal FastAPI `/api/query` endpoint
3. Integrate SourceBadge into React QueryInterface component
4. Test end-to-end with real queries
5. Create chart generation pipeline

See [UX_ENHANCEMENT_PLAN.md](./UX_ENHANCEMENT_PLAN.md) for detailed roadmap.
