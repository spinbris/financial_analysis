# Integration Plan - Executive Summary

**Date**: 2025-11-10
**Status**: Ready to Begin
**Timeline**: 3 weeks to production

---

## Overview

Integrate three repositories into a production system:
1. **financial_analysis** (this repo) - Python/Gradio backend
2. **Gradioappfrontend** - React/TypeScript frontend (Figma design)
3. **sjp-consulting-site** - Next.js marketing website

---

## Architecture

```
sjpconsulting.com (Next.js on Vercel - FREE)
    ↓ link to analysis tool
analysis.sjpconsulting.com (React on Vercel - FREE)
    ↓ REST API
Modal Platform ($10-30/month):
    ├─ FastAPI Bridge (modal_fastapi_bridge.py)
    ├─ Gradio Backend (existing)
    └─ ChromaDB (shared storage)
```

---

## Key Principles

### 1. Data-Driven, Not Design-Driven ✅
- Let data structure drive UI (not Figma specs)
- Your RAGResponse is already perfect for React
- Adapt Figma to showcase rich source data

### 2. Source Verifiability First ✅
- Every answer cites SEC EDGAR sources
- Display sources prominently (not hidden!)
- Show confidence, data age, limitations
- Competitive advantage over tools that don't cite sources

### 3. User-Provided API Keys (CRITICAL) ✅
- OpenAI costs: ~$1.50/analysis
- System-provided keys unsustainable ($450/mo for 100 users)
- User provides their own key → Your cost: $0
- Session-only storage, never persisted

### 4. Web Search Already Built ✅
- Brave Search integration exists, just needs UI toggle
- KB first, web fallback (only when insufficient/stale)
- Clear citation distinction (SEC vs web sources)

---

## What's Already Done

✅ **Backend Intelligence** (Phase 1 complete)
- SEC filing freshness detection
- Company status checking
- Web search fallback logic

✅ **UX Redesign** (Phase 2 complete)
- Company-centric dashboard
- Enhanced company lookup (names or tickers)
- Flexible dropdown with custom values
- Streamlined event handlers

✅ **Rich Data Structure**
- RAGResponse with sources_cited, confidence, limitations
- ChromaDB metadata with full provenance
- No adapter layer needed!

✅ **Integration Documentation**
- modal_fastapi_bridge.py ready to deploy
- react_api_integration.ts ready to use
- example_component.tsx pattern to follow

---

## What's NOT Done (Yet)

❌ **Groq Integration** - Attempted but not compatible with Agent SDK
- Agent SDK strips "openai/" prefix from GPT-OSS models
- Reverted to OpenAI GPT-5
- See [docs/GROQ_INTEGRATION_STATUS.md](docs/GROQ_INTEGRATION_STATUS.md)

❌ **React Integration** - Not started
- FastAPI bridge not deployed
- React frontend not connected
- User API key input not built

❌ **Production Deployment** - Not started
- Not on Vercel
- No custom domain configured
- Main website not updated

---

## 3-Week Roadmap

### Week 1: Modal + React + User Keys (5 days)

**Goal**: Working React app querying Modal API

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Deploy Modal FastAPI bridge | /api/health working |
| 2 | Set up React frontend | localhost:3000 loads |
| 3-4 | User-provided API keys | Session-only storage |
| 5 | Web search toggle | Checkbox enables Brave |

**Success criteria**: Query "What is AAPL's revenue?" from React UI with user's OpenAI key

---

### Week 2: Source-Rich UI (5 days)

**Goal**: Beautiful UI showcasing verifiable sources

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Prominent source display | Dedicated source card |
| 3 | Expandable source metadata | Accordion with chunk details |
| 4 | Figma updates | Design matches data structure |
| 5 | Polish & testing | Bug-free, smooth UX |

**Success criteria**: Users see SEC EDGAR citations prominently, trust the data

---

### Week 3: Production Deployment (5 days)

**Goal**: Live at analysis.sjpconsulting.com

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Deploy React to Vercel | analysis.sjpconsulting.com live |
| 2 | Configure domains & CORS | Custom domain working |
| 3 | Deploy main website | sjp-consulting-site.com updated |
| 4 | End-to-end testing | Full user flow works |
| 5 | Documentation & launch | User docs + announcement |

**Success criteria**: End-to-end flow works in production

---

## Cost Structure (With User-Provided Keys)

### Infrastructure Costs (You Pay)

| Service | Cost |
|---------|------|
| Modal (FastAPI + Gradio + ChromaDB) | $10-30/month |
| Vercel (React frontend) | FREE |
| Vercel (Next.js site) | FREE |
| Domain | ~$15/year |
| **Total** | **$10-30/month** |

### Analysis Costs (User Pays)

| Provider | Per Analysis | Who Pays |
|----------|--------------|----------|
| OpenAI GPT-5 | ~$1.50 | **User** (via their API key) |
| Brave Search (optional) | ~$0.015 | **You** (cheap!) |

**Your ongoing cost**: ~$10-30/month regardless of usage
**User cost**: ~$1.50/analysis (they pay OpenAI directly)

---

## Critical Success Factors

### 1. User-Provided Keys (REQUIRED)

Without Groq, OpenAI costs make system-provided keys unsustainable:

| Scenario | 100 Users | 1000 Users |
|----------|-----------|------------|
| System provides keys (3 free/mo) | $450/month | $4,500/month |
| User provides keys | $0/month | $0/month |

**Decision**: Make user-provided keys **required** (not optional)

### 2. Source Verifiability (COMPETITIVE ADVANTAGE)

Most financial tools don't show sources clearly. Yours does:
- SEC filing type (10-K, 10-Q)
- Specific period (Q3 FY2024)
- Section name
- Relevance score
- Timestamp

**UI Strategy**: Make sources PROMINENT, not hidden

### 3. Web Search (USER OPT-IN)

Already built, just needs React checkbox:
- Disabled by default (trust SEC data first)
- User enables when needed (real-time data)
- Clear source distinction (KB vs web)

---

## Integration Files Location

All ready in [docs/integration/](docs/integration/):

1. **START_HERE.md** - Overview (read this)
2. **MODAL_QUICK_START.md** - 30-minute setup guide
3. **modal_fastapi_bridge.py** - Deploy this to Modal
4. **react_api_integration.ts** - Copy to React src/api/
5. **example_component.tsx** - Follow this pattern
6. **INTEGRATION_ARCHITECTURE.md** - Detailed architecture
7. **IMPLEMENTATION_ROADMAP.md** - 3-week timeline

---

## Quick Start (30 Minutes)

### Step 1: Deploy Modal FastAPI (10 min)

```bash
cd financial_analysis
# Copy modal_fastapi_bridge.py from docs/integration/
modal run modal_fastapi_bridge.py  # Test
modal deploy modal_fastapi_bridge.py  # Deploy

# Save the URL:
# https://YOUR-USERNAME--sjp-financial-api-fastapi-app.modal.run
```

### Step 2: React Frontend (10 min)

```bash
cd Gradioappfrontend
mkdir -p src/api
# Copy react_api_integration.ts → src/api/integration.ts

# Create .env.local:
echo "VITE_API_URL=https://YOUR-USERNAME--sjp-financial-api-fastapi-app.modal.run" > .env.local
echo "VITE_API_TIMEOUT=60000" >> .env.local

npm install && npm run dev
# Visit http://localhost:3000
```

### Step 3: Test (10 min)

```bash
# Generate test data:
cd financial_analysis
python launch_web_app.py
# Visit http://localhost:7860
# Run analysis for AAPL

# Test React app:
# Go to http://localhost:3000
# Query "What is AAPL's revenue?"
```

---

## Alignment with DevNotes

**DevNotes**: [DEVNOTES_UPDATED_RECOMMENDATIONS.md](DEVNOTES_UPDATED_RECOMMENDATIONS.md)
**Integration Plan**: [UX_REDESIGN_PROPOSAL.md](UX_REDESIGN_PROPOSAL.md)

### Perfect Alignment ✅

| Feature | DevNotes | Integration Plan | Status |
|---------|----------|------------------|--------|
| User-provided keys | Session-only, critical | Required for sustainability | ✅ Aligned |
| Web search (Brave) | Reuse existing, opt-in | Checkbox toggle | ✅ Aligned |
| Source verifiability | Clear SEC vs web | Prominent display | ✅ Aligned |
| Data-driven UI | Let data define UI | Figma adapts to data | ✅ Aligned |
| Groq integration | ❌ Not compatible | ❌ On hold | ✅ Aligned |
| 20-F support | Phase 2 (future) | Phase 2 (future) | ✅ Aligned |

---

## Risk Mitigation

### Risk 1: User Refuses to Provide API Key

**Mitigation**:
- Clear explanation of why (cost transparency)
- Instructions for getting OpenAI key
- Emphasis on security (session-only, never stored)
- Maybe offer 1-2 free analyses with system key (demo only)

### Risk 2: Figma Design Doesn't Match Data

**Mitigation**:
- **Principle**: Data drives UI, not Figma
- Update Figma to showcase source richness
- Start with simple display, enhance incrementally

### Risk 3: Modal/Vercel Costs Higher Than Expected

**Mitigation**:
- Modal: Auto-scales, only pay for usage
- Vercel: Free tier very generous
- Monitor costs weekly in Month 1

---

## Success Metrics

### Week 1 Success
- [ ] Modal FastAPI deployed and responding
- [ ] React app connects to Modal API
- [ ] User can provide OpenAI key
- [ ] Query returns RAGResponse with sources

### Week 2 Success
- [ ] Sources displayed prominently (not hidden)
- [ ] Confidence badges visible
- [ ] Data age warnings show when stale
- [ ] Expandable raw source metadata works

### Week 3 Success
- [ ] analysis.sjpconsulting.com live
- [ ] Custom domain configured with SSL
- [ ] End-to-end user flow works
- [ ] Main website links to analysis tool

---

## Next Action

**Start Week 1, Day 1**: Deploy Modal FastAPI Bridge

```bash
cd financial_analysis
# Get modal_fastapi_bridge.py from docs/integration/
modal deploy modal_fastapi_bridge.py
```

**Expected time**: 10 minutes
**Expected outcome**: Working /api/health endpoint

---

**Last Updated**: 2025-11-10
**Ready to Begin**: ✅ YES
