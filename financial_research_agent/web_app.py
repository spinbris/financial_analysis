"""
Gradio web interface for Financial Research Agent.

Provides a professional, Morningstar-inspired UI for generating investment-grade
financial analysis reports.
"""

import gradio as gr
import asyncio
from pathlib import Path
from datetime import datetime
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from financial_research_agent.manager_enhanced import EnhancedFinancialResearchManager


# Morningstar-inspired theme
def create_theme():
    """Create a professional Morningstar-style theme."""
    return gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="slate",
        neutral_hue="slate",
    ).set(
        body_background_fill="#f5f7fa",
        body_text_color="#1a1d1f",
        block_background_fill="white",
        block_border_color="#e0e4e8",
        block_border_width="1px",
        block_label_background_fill="white",
        block_label_text_color="#1a1d1f",
        block_title_text_color="#1a1d1f",
        button_primary_background_fill="#0066cc",
        button_primary_background_fill_hover="#0052a3",
        button_primary_text_color="white",
        button_secondary_background_fill="#f0f2f5",
        button_secondary_text_color="#1a1d1f",
        input_background_fill="white",
        input_border_color="#d0d5dd",
    )


# KB Query examples
KB_QUERY_EXAMPLES = [
    "What are Apple's main revenue sources?",
    "Compare Microsoft and Google's cloud strategies",
    "What are Tesla's key financial risks?",
    "How has Amazon's profitability changed over time?",
    "Compare capex spend among AAPL, MSFT, GOOGL, META, NVDA",
    "Compare profit margins for Apple, Microsoft, Nvidia, Meta, Tesla",
]


class WebApp:
    """Gradio web application for Financial Research Agent."""

    def __init__(self):
        self.manager = None
        self.current_session_dir = None
        self.current_reports = {}
        self.analysis_map = {}  # Map labels to directory paths
        self.session_id = None  # For API key management
        self.llm_provider = "openai"  # Only provider supported after simplification

    def get_existing_analyses(self):
        """Get list of existing analysis directories with company names."""
        from financial_research_agent.config import AgentConfig
        output_dir = Path(AgentConfig.OUTPUT_DIR)
        if not output_dir.exists():
            return []

        # Find all analysis directories (format: YYYYMMDD_HHMMSS)
        dirs = sorted(
            [d for d in output_dir.iterdir() if d.is_dir() and d.name[0].isdigit()],
            key=lambda x: x.name,
            reverse=True  # Most recent first
        )

        # Extract company name and ticker from 00_query.md
        analyses = []
        for dir_path in dirs[:50]:  # Limit to 50 most recent
            query_file = dir_path / "00_query.md"
            comprehensive_file = dir_path / "07_comprehensive_report.md"

            # Check if analysis is complete
            if comprehensive_file.exists():
                # Try to extract company name and ticker from metadata.json (preferred)
                ticker = "Unknown"
                company_name = None

                # First, try to read from metadata.json
                metadata_file = dir_path / "metadata.json"
                if metadata_file.exists():
                    try:
                        import json
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                            ticker = metadata.get('ticker', 'Unknown')
                            company_name = metadata.get('company_name')
                    except Exception:
                        pass  # Fall through to query file parsing

                # Fallback to query file extraction if metadata not available
                if ticker == "Unknown" and query_file.exists():
                    content = query_file.read_text()

                    # Use the sophisticated ticker extraction from utils.py
                    from financial_research_agent.rag.utils import extract_tickers_from_query
                    detected_tickers = extract_tickers_from_query(content)
                    if detected_tickers:
                        ticker = detected_tickers[0]  # Use first detected ticker
                    else:
                        # Fallback to regex pattern for explicit tickers (e.g., "AAPL", "BRK.B")
                        import re
                        match = re.search(r'\b([A-Z]{1,5}(?:\.[A-Z])?)\b', content)
                        if match:
                            ticker = match.group(1)

                # Create a nice label with company name and ticker
                if company_name:
                    # Format: "Apple Inc. (AAPL)" or "WESTPAC BANKING CORP (WBKCY)"
                    label = f"{company_name} ({ticker})"
                else:
                    # Fallback to just ticker if no company name available
                    label = ticker

                analyses.append({
                    'label': label,
                    'value': str(dir_path),
                    'ticker': ticker,
                    'company_name': company_name,
                    'timestamp': dir_path.name
                })

        # Deduplicate by ticker - keep most recent for each ticker
        seen_tickers = {}
        for analysis in analyses:
            ticker_key = analysis['ticker']
            if ticker_key not in seen_tickers or analysis['timestamp'] > seen_tickers[ticker_key]['timestamp']:
                seen_tickers[ticker_key] = analysis

        # Convert back to list and sort alphabetically by ticker
        unique_analyses = list(seen_tickers.values())
        unique_analyses.sort(key=lambda x: x['ticker'])
        return unique_analyses

    def refresh_dropdown_choices(self):
        """Refresh the dropdown with latest analyses."""
        from financial_research_agent.config import AgentConfig
        analyses = self.get_existing_analyses()
        choices = [a['label'] for a in analyses]
        self.analysis_map = {a['label']: a['value'] for a in analyses}

        # Debug logging
        output_dir = Path(AgentConfig.OUTPUT_DIR)
        print(f"🔍 Refresh dropdown: OUTPUT_DIR={output_dir}, exists={output_dir.exists()}")
        print(f"🔍 Found {len(analyses)} analyses, {len(choices)} choices")
        if choices:
            print(f"🔍 Choices: {choices}")

        return gr.update(choices=choices)

    def load_existing_analysis(self, selected_label: str):
        """Load an existing analysis from disk."""
        from financial_research_agent.rag.utils import format_analysis_age
        import json
        import plotly.graph_objects as go

        # Auto-refresh analysis_map if selection is not in map
        if not selected_label:
            return ("", "", "", "", "", "", "", "", "", "", None, None, None, gr.update(visible=False))

        if selected_label not in self.analysis_map:
            print(f"⚠️ '{selected_label}' not in analysis_map, refreshing...")
            analyses = self.get_existing_analyses()
            self.analysis_map = {a['label']: a['value'] for a in analyses}

        if selected_label not in self.analysis_map:
            return (
                f"❌ Analysis '{selected_label}' not found in {AgentConfig.OUTPUT_DIR}",
                "", "", "", "", "", "", "", "", "", None, None, None, gr.update(visible=False)
            )

        analysis_path = self.analysis_map[selected_label]
        dir_path = Path(analysis_path)
        if not dir_path.exists():
            return (
                "❌ Analysis directory not found",
                "", "", "", "", "", "", "", "", "", None, None, None, gr.update(visible=False)
            )

        # Set current session directory for cost summary loading
        self.current_session_dir = dir_path

        # Load report files
        reports = {}
        file_map = {
            'comprehensive': '07_comprehensive_report.md',
            'statements': '03_financial_statements.md',
            'metrics': '04_financial_metrics.md',
            'banking_ratios': '04_banking_ratios.md',  # Banking-specific ratios (conditional)
            'financial_analysis': '05_financial_analysis.md',
            'risk_analysis': '06_risk_analysis.md',
            'verification': '08_verification.md',
            'cost_report': '09_cost_report.md',
            'search_results': '02_search_results.md',
            'edgar_filings': '02_edgar_filings.md'
        }

        for key, filename in file_map.items():
            file_path = dir_path / filename
            if file_path.exists():
                reports[key] = file_path.read_text()
            else:
                # Don't mark banking_ratios as "not found" - it's conditional
                if key == 'banking_ratios':
                    reports[key] = None
                else:
                    reports[key] = f"*{filename} not found*"

        # Load chart data (if available) and convert to Plotly Figure objects
        margin_chart_fig = None
        metrics_chart_fig = None
        risk_chart_fig = None

        # Revenue & Profitability chart (repurposed margin_chart slot)
        revenue_chart_path = dir_path / "chart_revenue_profitability.json"
        if revenue_chart_path.exists():
            try:
                with open(revenue_chart_path, 'r') as f:
                    revenue_chart_data = json.load(f)
                margin_chart_fig = go.Figure(revenue_chart_data)
            except Exception as e:
                print(f"Warning: Failed to load revenue chart: {e}")

        # Margin Trends chart (repurposed metrics_chart slot)
        margin_trends_path = dir_path / "chart_margins.json"
        if margin_trends_path.exists():
            try:
                with open(margin_trends_path, 'r') as f:
                    margin_trends_data = json.load(f)
                metrics_chart_fig = go.Figure(margin_trends_data)
            except Exception as e:
                print(f"Warning: Failed to load margin trends chart: {e}")

        # Balance Sheet chart (repurposed risk_chart slot)
        balance_sheet_path = dir_path / "chart_balance_sheet.json"
        if balance_sheet_path.exists():
            try:
                with open(balance_sheet_path, 'r') as f:
                    balance_sheet_data = json.load(f)
                risk_chart_fig = go.Figure(balance_sheet_data)
            except Exception as e:
                print(f"Warning: Failed to load balance sheet chart: {e}")

        # Format timestamp with human-readable date
        age_info = format_analysis_age(dir_path.name)

        # Load cost summary
        cost_summary = self._load_cost_summary()
        cost_line = f"\n{cost_summary}\n" if cost_summary else ""

        status_msg = f"""✅ Loaded analysis successfully!

**Analysis Date:** {age_info['formatted']} {age_info['status_emoji']}
**Session ID:** {dir_path.name}
{cost_line}"""

        # Check if banking ratios exist (banking sector analysis)
        has_banking_ratios = reports.get('banking_ratios') is not None

        return (
            status_msg,
            reports.get('comprehensive', ''),
            reports.get('statements', ''),
            reports.get('metrics', ''),
            reports.get('banking_ratios', '*Banking ratios not available for this company (non-banking sector)*'),
            reports.get('financial_analysis', ''),
            reports.get('risk_analysis', ''),
            reports.get('verification', ''),
            reports.get('cost_report', '*Cost report not available for this analysis*'),
            reports.get('search_results', '*Search results not available for this analysis*'),
            reports.get('edgar_filings', '*EDGAR filings data not available for this analysis*'),
            margin_chart_fig,
            metrics_chart_fig,
            risk_chart_fig,
            gr.update(visible=has_banking_ratios)  # Show banking tab only if banking ratios exist
        )

    def query_knowledge_base(
        self,
        query: str,
        ticker_filter: str = "",
        analysis_type: str = "",
        num_results: int = 5
    ):
        """
        Query the ChromaDB knowledge base with semantic search and synthesis.

        Uses the RAG synthesis agent to provide coherent, well-cited answers
        instead of raw document chunks.

        Args:
            query: Natural language search query
            ticker_filter: Optional ticker to filter results
            analysis_type: Optional analysis type filter
            num_results: Number of results to return

        Yields:
            Formatted markdown with synthesized answer, sources, and confidence
        """
        from financial_research_agent.rag.chroma_manager import FinancialRAGManager
        from financial_research_agent.rag.utils import extract_tickers_from_query

        if not query or query.strip() == "":
            yield "❌ Please enter a search query"
            return

        # Show initial progress
        yield "🔍 Analyzing query..."

        try:
            # Initialize ChromaDB
            from financial_research_agent.config import AgentConfig
            rag = FinancialRAGManager(persist_directory=AgentConfig.CHROMA_DB_DIR)

            # Extract tickers from query if not explicitly filtered
            if not ticker_filter:
                detected_tickers = extract_tickers_from_query(query)

                # Filter out tickers that aren't in KB (reduces false positives like "MAIN")
                # Only keep tickers we actually have data for
                if detected_tickers:
                    kb_tickers = [t for t in detected_tickers if rag.check_company_status(t)["in_kb"]]
                    # If we filtered everything out, keep original list for routing logic to handle
                    detected_tickers = kb_tickers if kb_tickers else detected_tickers
            else:
                detected_tickers = [ticker_filter.strip().upper()]

            # Use smart routing to decide how to handle the query
            from financial_research_agent.rag.intelligence import (
                decide_query_routing,
                format_query_decision_prompt
            )

            decision = decide_query_routing(
                detected_tickers=detected_tickers,
                chroma_manager=rag,
                require_fresh=False  # Allow aging data for queries
            )

            # If we should suggest analysis instead of querying, show the prompt
            if decision.action == "suggest_analysis":
                yield "📊 Checking knowledge base status..."
                kb_companies = rag.get_companies_with_status()
                prompt = format_query_decision_prompt(decision, query, kb_companies)
                if prompt:
                    yield prompt
                    return

            # If we have mixed quality data, show a warning but allow proceeding
            if decision.action == "mixed_quality":
                yield "⚠️ Checking data quality..."
                kb_companies = rag.get_companies_with_status()
                prompt = format_query_decision_prompt(decision, query, kb_companies)
                if prompt:
                    yield prompt
                    return

            # Show searching progress
            yield "🔍 Searching knowledge base..."

            # Prepare filters
            ticker = ticker_filter.strip().upper() if ticker_filter else None
            analysis_type_val = analysis_type if analysis_type else None

            # Multi-company comparison strategy: If multiple tickers detected and no explicit filter,
            # query each company separately to ensure balanced representation
            if not ticker and detected_tickers and len(detected_tickers) >= 2:
                # Per-company strategy for fair comparison
                yield "🤖 Querying each company separately for balanced comparison..."

                # Query each ticker separately with fewer results per company
                results_per_company = max(3, num_results // len(detected_tickers))
                combined_results = {
                    'documents': [[]],
                    'metadatas': [[]],
                    'distances': [[]]
                }

                # For numerical comparison queries, prioritize financial_metrics
                query_lower = query.lower()
                numerical_keywords = ['margin', 'ratio', 'revenue', 'profit', 'income', 'earnings',
                                     'cash', 'debt', 'equity', 'assets', 'compare']
                prefer_metrics = any(keyword in query_lower for keyword in numerical_keywords)

                for ticker_symbol in detected_tickers:
                    # If this is a numerical comparison, first try to get financial_metrics
                    if prefer_metrics and not analysis_type_val:
                        metrics_results = rag.query(
                            query=query,
                            ticker=ticker_symbol,
                            analysis_type='financial_metrics',
                            n_results=2
                        )
                        # Get one more general result for context
                        general_results = rag.query(
                            query=query,
                            ticker=ticker_symbol,
                            analysis_type=None,
                            n_results=1
                        )

                        # Combine metrics + general
                        if metrics_results and 'documents' in metrics_results:
                            combined_results['documents'][0].extend(metrics_results['documents'][0])
                            combined_results['metadatas'][0].extend(metrics_results['metadatas'][0])
                            combined_results['distances'][0].extend(metrics_results['distances'][0])
                        if general_results and 'documents' in general_results:
                            combined_results['documents'][0].extend(general_results['documents'][0])
                            combined_results['metadatas'][0].extend(general_results['metadatas'][0])
                            combined_results['distances'][0].extend(general_results['distances'][0])
                    else:
                        # Standard query
                        company_results = rag.query(
                            query=query,
                            ticker=ticker_symbol,
                            analysis_type=analysis_type_val,
                            n_results=results_per_company
                        )

                        # Combine results
                        if company_results and 'documents' in company_results:
                            combined_results['documents'][0].extend(company_results['documents'][0])
                            combined_results['metadatas'][0].extend(company_results['metadatas'][0])
                            combined_results['distances'][0].extend(company_results['distances'][0])

                # Check if we need to supplement with web search
                web_search_used = []
                web_search_errors = []
                if self._should_use_web_search(query, combined_results, detected_tickers):
                    yield "🌐 Supplementing with web search for recent data..."
                    web_search_used, web_search_errors = self._supplement_with_web_search(
                        query, combined_results, detected_tickers
                    )

                # Synthesize the combined results
                from financial_research_agent.rag.synthesis_agent import synthesize_rag_results
                yield "🤖 Synthesizing answer from sources..."
                # Use higher max_turns (10) when web search is enabled to allow for tool calls
                # Standard synthesis (3 turns) is too low when agent needs to call web search
                response = synthesize_rag_results(query, combined_results, max_turns=10)
            else:
                # Single company or explicit filter - use standard query
                yield "🤖 Synthesizing answer from sources..."
                response = rag.query_with_synthesis(
                    query=query,
                    ticker=ticker,
                    analysis_type=analysis_type_val,
                    n_results=num_results
                )

            # Format synthesized response as markdown
            output = f"# 💡 Answer\n\n"

            # Add web search notification if used
            if 'web_search_used' in locals() and web_search_used:
                output += f"ℹ️ *Supplemented with web search for: {', '.join(web_search_used)}*\n\n"

            # Add web search errors if any
            if 'web_search_errors' in locals() and web_search_errors:
                output += f"⚠️ **Web search issues:**\n"
                for error in web_search_errors:
                    output += f"  - {error}\n"
                output += "\n"

            # Add filter context
            if ticker or analysis_type_val:
                output += "*Filtered by: "
                filters = []
                if ticker:
                    filters.append(f"Ticker: {ticker}")
                if analysis_type_val:
                    filters.append(f"Type: {analysis_type_val}")
                output += ", ".join(filters) + "*\n\n"

            # Main synthesized answer
            output += response.answer + "\n\n"

            # Confidence indicator
            output += "---\n\n"
            confidence_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}
            emoji = confidence_emoji.get(response.confidence.lower(), "⚪")
            output += f"**Confidence:** {emoji} {response.confidence.upper()}\n\n"

            # Data age warning (if present)
            if response.data_age_warning:
                output += f"### ⏰ Data Age Notice\n\n{response.data_age_warning}\n\n"
                output += "*Consider running a fresh analysis if you need the most current data.*\n\n"

            # Sources cited
            if response.sources_cited:
                output += "### 📚 Sources\n\n"
                for i, source in enumerate(response.sources_cited, 1):
                    output += f"{i}. {source}\n"
                output += "\n"

            # Limitations/caveats
            if response.limitations:
                output += f"### ⚠️ Limitations\n\n{response.limitations}\n\n"

            # Suggested follow-up questions
            if response.suggested_followup:
                output += "### 💭 Suggested Follow-up Questions\n\n"
                for question in response.suggested_followup:
                    output += f"- {question}\n"
                output += "\n"

            output += "---\n\n*💡 Tip: Click a suggested question to explore further*"

            yield output

        except FileNotFoundError:
            yield "### 📂 ChromaDB Not Found\n\nThe knowledge base has not been initialized yet.\n\nTo populate it:\n1. Run analyses using the \"Run New Analysis\" mode\n2. Or run: `python scripts/upload_local_to_chroma.py --ticker AAPL --analysis-dir <path>`\n\n See `chroma_db/` directory."
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            yield f"### ❌ Error\n\nFailed to query knowledge base:\n\n```\n{str(e)}\n```\n\n<details>\n<summary>Full Error Details</summary>\n\n```\n{error_detail}\n```\n</details>"

    def _should_use_web_search(
        self,
        query: str,
        kb_results: dict,
        detected_tickers: list[str]
    ) -> bool:
        """
        Determine if web search should be used to supplement KB results.

        Args:
            query: User's query string
            kb_results: ChromaDB results with documents, metadatas, distances
            detected_tickers: List of tickers detected in query

        Returns:
            True if web search should be triggered
        """
        # Time-sensitive keywords that suggest we need recent data
        time_sensitive_keywords = [
            'current', 'latest', 'recent', '2024', '2025', 'spend', 'spending',
            'capex', 'investment', 'ai', 'guidance', 'forecast'
        ]
        query_lower = query.lower()
        is_time_sensitive = any(keyword in query_lower for keyword in time_sensitive_keywords)

        # Check if KB results are sparse
        total_chunks = len(kb_results.get('documents', [[]])[0])
        expected_chunks = len(detected_tickers) * 2  # Expect at least 2 chunks per company
        is_sparse = total_chunks < expected_chunks

        # Use web search if query is time-sensitive OR results are sparse
        return is_time_sensitive or is_sparse

    def _supplement_with_web_search(
        self,
        query: str,
        kb_results: dict,
        detected_tickers: list[str]
    ) -> tuple[list[str], list[str]]:
        """
        Supplement KB results with web search data.

        Args:
            query: User's original query
            kb_results: Existing KB results to supplement (modified in-place)
            detected_tickers: List of tickers to search for

        Returns:
            Tuple of (successful_tickers, error_messages)
        """
        from datetime import datetime
        import asyncio
        import httpx
        import os
        import traceback

        web_search_tickers = []
        error_messages = []

        # Extract topic from query (remove company names and common words)
        topic_words = []
        skip_words = {'compare', 'what', 'how', 'is', 'are', 'the', 'and', 'or', 'among', 'across'}
        for word in query.lower().split():
            if (word not in skip_words and
                len(word) > 2 and
                not any(ticker.lower() in word for ticker in detected_tickers)):
                topic_words.append(word)
        topic = ' '.join(topic_words[:5])  # Limit to 5 most relevant words

        # Helper to run async search with retry logic
        async def search_ticker(ticker: str, semaphore: asyncio.Semaphore):
            async with semaphore:  # Limit concurrent requests
                max_retries = 3

                for attempt in range(max_retries):
                    try:
                        # Build search query: "TICKER topic 2024 2025"
                        search_query = f"{ticker} {topic} 2024 2025"

                        # Call Brave Search API directly
                        api_key = os.getenv("BRAVE_API_KEY")
                        if not api_key:
                            error_msg = f"{ticker}: No BRAVE_API_KEY configured"
                            error_messages.append(error_msg)
                            return ("error", ticker, error_msg)

                        headers = {
                            "Accept": "application/json",
                            "Accept-Encoding": "gzip",
                            "X-Subscription-Token": api_key
                        }

                        params = {
                            "q": search_query,
                            "count": 2,
                            "text_decorations": False,
                            "search_lang": "en",
                            "result_filter": "web"
                        }

                        async with httpx.AsyncClient(timeout=30.0) as client:
                            response = await client.get(
                                "https://api.search.brave.com/res/v1/web/search",
                                headers=headers,
                                params=params,
                                follow_redirects=True
                            )
                            response.raise_for_status()
                            data = response.json()

                            # Extract results
                            web_results = data.get("web", {}).get("results", [])

                            if not web_results:
                                error_msg = f"{ticker}: No web results found for '{search_query}'"
                                error_messages.append(error_msg)
                                return ("error", ticker, error_msg)

                            # Add small delay between successful requests to avoid rate limits
                            await asyncio.sleep(0.5)
                            return ("success", ticker, web_results[:2])

                    except httpx.HTTPStatusError as e:
                        if e.response.status_code == 429:
                            # Rate limit - retry with exponential backoff
                            if attempt < max_retries - 1:
                                backoff_delay = 2 ** attempt  # 1s, 2s, 4s
                                error_msg = f"{ticker}: HTTP 429 rate limit (attempt {attempt + 1}/{max_retries}), retrying in {backoff_delay}s..."
                                await asyncio.sleep(backoff_delay)
                                continue
                            else:
                                error_msg = f"{ticker}: HTTP 429 rate limit exceeded after {max_retries} attempts"
                                error_messages.append(error_msg)
                                return ("error", ticker, error_msg)
                        else:
                            error_msg = f"{ticker}: HTTP {e.response.status_code} - {str(e)}"
                            error_messages.append(error_msg)
                            return ("error", ticker, error_msg)

                    except httpx.TimeoutException as e:
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1)
                            continue
                        error_msg = f"{ticker}: Request timeout after {max_retries} attempts"
                        error_messages.append(error_msg)
                        return ("error", ticker, error_msg)

                    except Exception as e:
                        error_msg = f"{ticker}: {type(e).__name__}: {str(e)}"
                        error_messages.append(error_msg)
                        return ("error", ticker, error_msg)

        # Run searches for all tickers with concurrency limit
        async def search_all():
            # Limit to 2 concurrent searches to avoid rate limits
            semaphore = asyncio.Semaphore(2)
            tasks = [search_ticker(ticker, semaphore) for ticker in detected_tickers]
            return await asyncio.gather(*tasks, return_exceptions=True)

        # Execute searches
        try:
            results = asyncio.run(search_all())

            for result in results:
                # Handle exceptions caught by gather
                if isinstance(result, Exception):
                    error_msg = f"Unknown ticker: {type(result).__name__}: {str(result)}"
                    error_messages.append(error_msg)
                    continue

                # Unpack the tuple (status, ticker, data)
                if not isinstance(result, tuple) or len(result) != 3:
                    error_msg = f"Invalid result format: {result}"
                    error_messages.append(error_msg)
                    continue

                status, ticker, data = result

                if status == "success":
                    # data is a list of web results
                    if not isinstance(data, list):
                        error_msg = f"{ticker}: Expected list of web results, got {type(data)}"
                        error_messages.append(error_msg)
                        continue

                    # Add search results as synthetic KB chunks
                    for web_result in data:
                        # Extract title and description
                        title = web_result.get('title', '')
                        description = web_result.get('description', '')
                        content = f"{title}\n\n{description}"

                        # Add to KB results
                        kb_results['documents'][0].append(content)
                        kb_results['metadatas'][0].append({
                            'ticker': ticker,
                            'analysis_type': 'web_search',
                            'source': 'Brave Search',
                            'url': web_result.get('url', ''),
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'section': f'Web Search: {topic}'
                        })
                        kb_results['distances'][0].append(0.0)  # Treat as highly relevant

                    web_search_tickers.append(ticker)
                # Errors already recorded in error_messages

        except Exception as e:
            # Catch-all for asyncio.run failures
            error_msg = f"Web search system error: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            error_messages.append(error_msg)

        return web_search_tickers, error_messages

    def _extract_ticker_from_query(self, query: str) -> str | None:
        """
        Extract ticker symbol from query using existing RAG utility.

        This enables sector-specific features like banking ratios analysis.

        Args:
            query: User query string (e.g., "JPM", "Analyze JPMorgan Chase", "AAPL Q3 2024")

        Returns:
            Extracted ticker symbol or None if no ticker detected
        """
        from financial_research_agent.rag.utils import extract_tickers_from_query
        detected_tickers = extract_tickers_from_query(query)
        return detected_tickers[0] if detected_tickers else None

    async def generate_analysis(
        self,
        query: str,
        progress=gr.Progress()
    ):
        """
        Generate financial analysis from query with streaming updates.

        Yields:
            Tuple of (status_message, comprehensive_report, financial_statements,
                     financial_metrics, data_verification)
        """
        if not query or query.strip() == "":
            yield (
                "❌ Please enter a query or select a template",
                "", "", "", "", "", "", "", "", "", "", None, None, None, gr.update(visible=False)
            )
            return

        try:
            # Reset session directory for new analysis (prevents showing old reports)
            self.current_session_dir = None
            self.manager = None

            # Initialize empty reports
            reports = {
                'comprehensive': '*⏳ Waiting for comprehensive report...*',
                'statements': '*⏳ Waiting for financial statements...*',
                'metrics': '*⏳ Waiting for financial metrics...*',
                'banking_ratios': None,  # Will be set if banking sector
                'financial_analysis': '*⏳ Waiting for financial analysis...*',
                'risk_analysis': '*⏳ Waiting for risk analysis...*',
                'verification': '*⏳ Waiting for verification...*',
                'cost_report': '*⏳ Waiting for cost report...*',
                'search_results': '*⏳ Waiting for search results...*',
                'edgar_filings': '*⏳ Waiting for EDGAR filings...*'
            }

            # Track which reports we've already loaded
            loaded_reports = set()

            # Define progress callback with streaming updates
            def progress_callback(prog: float, desc: str):
                progress(prog, desc=desc)

            # Configure OpenAI API key from session if available
            progress(0.0, desc="Configuring OpenAI...")
            import os
            from financial_research_agent.llm_provider import get_session_manager

            # Get OpenAI API key from session if available
            manager = get_session_manager()
            openai_key = None

            if self.session_id:
                openai_key = manager.get_api_key(self.session_id, "openai")

            # Set OpenAI API key if provided
            if openai_key:
                os.environ["OPENAI_API_KEY"] = openai_key

            # Clear any leftover OPENAI_BASE_URL from previous configurations
            if "OPENAI_BASE_URL" in os.environ:
                del os.environ["OPENAI_BASE_URL"]

            # Extract ticker from query before running analysis
            # This enables sector-specific features like banking ratios
            ticker = self._extract_ticker_from_query(query)

            # Initialize manager with progress callback
            progress(0.05, desc="Initializing analysis engine...")
            from financial_research_agent.config import AgentConfig
            self.manager = EnhancedFinancialResearchManager(
                output_dir=AgentConfig.OUTPUT_DIR,
                progress_callback=progress_callback
            )

            # Start the analysis in background with ticker parameter
            import asyncio
            analysis_task = asyncio.create_task(self.manager.run(query, ticker=ticker))

            # Poll for completed reports while analysis runs
            last_check = 0
            poll_count = 0
            while not analysis_task.done():
                # Check every 2 seconds for new reports
                await asyncio.sleep(2)
                poll_count += 1

                # Keep progress bar alive even if no updates
                # This prevents the timer from appearing frozen
                if poll_count % 5 == 0:  # Every 10 seconds
                    progress(None, desc="Analysis in progress...")

                if self.manager.session_dir and self.manager.session_dir.exists():
                    self.current_session_dir = self.manager.session_dir

                    # Check for new reports
                    new_reports = self._load_reports()
                    has_updates = False

                    for key, content in new_reports.items():
                        if (content is not None and
                            not content.startswith('*Report not generated:') and
                            key not in loaded_reports):
                            reports[key] = content
                            loaded_reports.add(key)
                            has_updates = True

                    # Yield update if we found new reports
                    if has_updates:
                        from financial_research_agent.rag.utils import format_analysis_age
                        age_info = format_analysis_age(self.current_session_dir.name)
                        status_msg = f"""🔄 Analysis in progress...

**Analysis Started:** {age_info['formatted']}
**Session ID:** {self.current_session_dir.name}
**Query:** {query}

**Completed Reports:** {', '.join(sorted(loaded_reports))}
"""

                        # Check if banking ratios exist
                        has_banking = reports.get('banking_ratios') is not None

                        yield (
                            status_msg,
                            reports.get('comprehensive', ''),
                            reports.get('statements', ''),
                            reports.get('metrics', ''),
                            reports.get('banking_ratios', '*Banking ratios not available (non-banking sector)*'),
                            reports.get('financial_analysis', ''),
                            reports.get('risk_analysis', ''),
                            reports.get('verification', ''),
                            reports.get('cost_report', '*⏳ Cost report being generated...*'),
                            reports.get('search_results', ''),
                            reports.get('edgar_filings', ''),
                            None,  # Charts not available yet
                            None,
                            None,
                            gr.update(visible=has_banking)  # Banking tab visibility
                        )

            # Wait for analysis to complete
            await analysis_task

            # Get the session directory that was created
            self.current_session_dir = self.manager.session_dir

            progress(0.95, desc="Loading final reports...")

            # Load all final reports
            reports = self._load_reports()

            # Auto-index to ChromaDB for instant Q&A
            progress(0.96, desc="Indexing to knowledge base...")
            try:
                from financial_research_agent.rag.chroma_manager import FinancialRAGManager
                from financial_research_agent.rag.utils import extract_tickers_from_query
                from financial_research_agent.config import AgentConfig

                # Extract ticker from query
                detected_tickers = extract_tickers_from_query(query)
                ticker = detected_tickers[0] if detected_tickers else "UNKNOWN"

                # Index the analysis
                rag = FinancialRAGManager(persist_directory=AgentConfig.CHROMA_DB_DIR)
                result = rag.index_analysis_from_directory(self.current_session_dir, ticker=ticker)
                print(f"✅ Indexed {result.get('total_chunks', 0)} chunks for {ticker} to ChromaDB at {AgentConfig.CHROMA_DB_DIR}")
            except Exception as index_error:
                # Don't fail the whole analysis if indexing fails
                print(f"❌ Warning: Failed to auto-index analysis: {index_error}")
                import traceback
                traceback.print_exc()

            # Auto-generate charts (optional - won't break if unavailable)
            progress(0.98, desc="Generating interactive charts...")
            margin_chart_fig = None
            metrics_chart_fig = None
            risk_chart_fig = None

            try:
                # Load the generated charts (charts are now generated during analysis by manager)
                import json
                import plotly.graph_objects as go

                # Revenue & Profitability chart (NEW)
                revenue_chart_path = self.current_session_dir / "chart_revenue_profitability.json"
                if revenue_chart_path.exists():
                    with open(revenue_chart_path, 'r') as f:
                        revenue_chart_data = json.load(f)
                    margin_chart_fig = go.Figure(revenue_chart_data)  # Use margin_chart_fig slot

                # Margin Trends chart
                margin_trends_path = self.current_session_dir / "chart_margins.json"
                if margin_trends_path.exists():
                    with open(margin_trends_path, 'r') as f:
                        margin_trends_data = json.load(f)
                    metrics_chart_fig = go.Figure(margin_trends_data)  # Use metrics_chart_fig slot

                # Balance Sheet chart (NEW)
                balance_sheet_path = self.current_session_dir / "chart_balance_sheet.json"
                if balance_sheet_path.exists():
                    with open(balance_sheet_path, 'r') as f:
                        balance_sheet_data = json.load(f)
                    risk_chart_fig = go.Figure(balance_sheet_data)  # Use risk_chart_fig slot
            except Exception as chart_error:
                # Don't fail the whole analysis if chart generation fails
                # Silently skip charts - they're optional enhancement, not core functionality
                pass  # Charts will remain None, which is handled gracefully by Gradio

            progress(1.0, desc="Complete!")

            from financial_research_agent.rag.utils import format_analysis_age
            age_info = format_analysis_age(self.current_session_dir.name)
            # Load cost summary
            cost_summary = self._load_cost_summary()
            cost_line = f"\n{cost_summary}\n" if cost_summary else ""

            status_msg = f"""✅ Analysis completed successfully!

**Analysis Date:** {age_info['formatted']} {age_info['status_emoji']}
**Session ID:** {self.current_session_dir.name}
**Query:** {query}
{cost_line}
📊 All reports are now available in the Reports tab. The analysis has been automatically indexed to the knowledge base for instant Q&A!
"""

            # Check if banking ratios exist (banking sector analysis)
            has_banking_ratios = reports.get('banking_ratios') is not None

            yield (
                status_msg,
                reports.get('comprehensive', ''),
                reports.get('statements', ''),
                reports.get('metrics', ''),
                reports.get('banking_ratios', '*Banking ratios not available (non-banking sector)*'),
                reports.get('financial_analysis', ''),
                reports.get('risk_analysis', ''),
                reports.get('verification', ''),
                reports.get('cost_report', '*Cost report not available for this analysis*'),
                reports.get('search_results', '*Search results not available for this analysis*'),
                reports.get('edgar_filings', '*EDGAR filings data not available for this analysis*'),
                margin_chart_fig,
                metrics_chart_fig,
                risk_chart_fig,
                gr.update(visible=has_banking_ratios)  # Show banking tab only if ratios exist
            )

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            error_msg = f"""❌ Error during analysis:

**Error:** {str(e)}

**Details:** See console for full traceback.

If this error persists, please check:
1. API keys are correctly set
2. Internet connection is available
3. SEC EDGAR is accessible
"""
            print(f"\n{'='*60}\nERROR IN ANALYSIS:\n{'='*60}\n{error_details}\n{'='*60}\n")
            yield (error_msg, "", "", "", "", "", "", "", "", "", "", None, None, None, gr.update(visible=False))

    def _load_cost_summary(self) -> str:
        """Load cost summary from cost_report.json for status display."""
        if not self.current_session_dir or not self.current_session_dir.exists():
            return ""

        cost_json_path = self.current_session_dir / "cost_report.json"
        if not cost_json_path.exists():
            return ""

        try:
            import json
            with open(cost_json_path, 'r') as f:
                cost_data = json.load(f)

            total_cost = cost_data.get('total_cost', 0)
            duration = cost_data.get('duration_seconds', 0)

            # Format duration
            if duration >= 60:
                duration_str = f"{duration/60:.1f} min"
            else:
                duration_str = f"{duration:.0f}s"

            return f"**💰 Cost:** ${total_cost:.4f} | **⏱️ Duration:** {duration_str}"
        except Exception:
            return ""

    def _load_reports(self) -> dict[str, str]:
        """Load generated markdown reports from session directory."""
        reports = {}

        if not self.current_session_dir or not self.current_session_dir.exists():
            return reports

        # Map report files to keys (using actual filenames from manager_enhanced.py)
        report_files = {
            'comprehensive': '07_comprehensive_report.md',
            'statements': '03_financial_statements.md',
            'metrics': '04_financial_metrics.md',
            'banking_ratios': '04_banking_ratios.md',  # Banking-specific (conditional)
            'financial_analysis': '05_financial_analysis.md',
            'risk_analysis': '06_risk_analysis.md',
            'verification': '08_verification.md',
            'search_results': '02_search_results.md',
            'edgar_filings': '02_edgar_filings.md',
            'cost_report': '09_cost_report.md',  # Cost breakdown
        }

        for key, filename in report_files.items():
            file_path = self.current_session_dir / filename
            if file_path.exists():
                reports[key] = file_path.read_text(encoding='utf-8')
                if key == 'cost_report':
                    print(f"✅ Loaded cost report from {file_path}")
            else:
                # Banking ratios is conditional - don't show "not generated" if it doesn't exist
                if key == 'banking_ratios':
                    reports[key] = None
                else:
                    reports[key] = f"*Report not generated: {filename}*"
                    if key == 'cost_report':
                        print(f"❌ Cost report NOT found at {file_path}")

        return reports

    def use_template(self, template_name: str) -> str:
        """Return the query for a selected template."""
        return QUERY_TEMPLATES.get(template_name, "")

    def _format_missing_companies_prompt(self, missing_tickers: list[str], query: str) -> str:
        """
        Format a helpful prompt when companies are not in knowledge base.

        Args:
            missing_tickers: List of tickers not in KB
            query: Original user query

        Returns:
            Formatted markdown guidance
        """
        if len(missing_tickers) == 1:
            ticker = missing_tickers[0]
            return f"""## ⚠️ Company Not in Knowledge Base

**{ticker}** has not been analyzed yet and is not in the knowledge base.

### To answer questions about {ticker}:

1. **Run a comprehensive analysis first** (Recommended)
   - Switch to the **"Run New Analysis"** mode
   - Enter query: `Analyze {ticker}'s most recent quarterly performance`
   - Time: ~3-5 minutes
   - Cost: ~$0.08
   - Includes: Complete SEC filings, 118+ line items, risk analysis

2. **Try a different company**
   - Query companies already in the knowledge base (see below)

---

### 📊 Companies Currently in Knowledge Base:

{self._format_kb_companies_list()}

---

*Once {ticker} is analyzed, you can ask unlimited questions about it instantly!*
"""
        else:
            ticker_list = ", ".join(missing_tickers)
            return f"""## ⚠️ Multiple Companies Not in Knowledge Base

The following companies are not yet in the knowledge base:
**{ticker_list}**

### To compare these companies:

1. **Analyze each company** (Recommended for accurate comparisons)
   - Switch to **"Run New Analysis"** mode
   - Analyze each ticker separately (or in sequence)
   - Total time: ~{len(missing_tickers) * 3}-{len(missing_tickers) * 5} minutes
   - Total cost: ~${len(missing_tickers) * 0.08:.2f}

2. **Partial comparison** (if some companies are in KB)
   - Refine your query to only include companies already analyzed

---

### 📊 Companies Currently in Knowledge Base:

{self._format_kb_companies_list()}

---

*Tip: Build up your knowledge base over time by analyzing companies as needed!*
"""

    def _format_kb_companies_list(self) -> str:
        """
        Get formatted list of companies in knowledge base.

        Returns:
            Markdown formatted list
        """
        from financial_research_agent.rag.chroma_manager import FinancialRAGManager
        from financial_research_agent.rag.utils import format_company_status
        from financial_research_agent.config import AgentConfig

        try:
            rag = FinancialRAGManager(persist_directory=AgentConfig.CHROMA_DB_DIR)
            companies = rag.get_companies_with_status()

            if not companies:
                return "*Knowledge base is empty. Run your first analysis!*"

            # Format as bullet list
            lines = []
            for company in companies[:20]:  # Limit to top 20
                lines.append(f"- {format_company_status(company)}")

            if len(companies) > 20:
                lines.append(f"\n*...and {len(companies) - 20} more companies*")

            return "\n".join(lines)

        except Exception:
            return "*Unable to load knowledge base status*"

    def save_session_keys(self, openai_key: str) -> str:
        """Save OpenAI API key for the current session."""
        from financial_research_agent.llm_provider import get_session_manager

        # Create session if needed
        if not self.session_id:
            manager = get_session_manager()
            self.session_id = manager.create_session()

        manager = get_session_manager()

        # Store OpenAI key
        if openai_key:
            manager.set_api_key(self.session_id, "openai", openai_key)
            return "✅ **OpenAI key saved**\n\n*Keys stored in-memory only. Remember to delete from provider after use!*"
        else:
            return "*Using environment/default OpenAI key*"

    def clear_session_keys(self) -> str:
        """Clear all session keys."""
        from financial_research_agent.llm_provider import get_session_manager

        if self.session_id:
            manager = get_session_manager()
            manager.clear_session(self.session_id)
            self.session_id = None
            return "✅ **Session keys cleared**\n\n*Remember to delete keys from your OpenAI account!*"
        else:
            return "*No session keys to clear*"

    def fetch_stock_price_chart(self, ticker: str, period: str = "1y"):
        """Fetch and generate stock price chart using yfinance."""
        try:
            if not ticker or ticker.strip() == "":
                return None, "", "Please enter a valid ticker symbol."

            ticker = ticker.strip().upper()

            # Fetch stock data
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)

            if hist.empty:
                return None, "", f"No data found for ticker '{ticker}'. Please check the symbol and try again."

            # Get company name and currency
            try:
                company_name = stock.info.get('longName', ticker)
                if not company_name or company_name == ticker:
                    company_name = stock.info.get('shortName', ticker)
                # Get currency from stock info
                currency = stock.info.get('currency', 'USD')
            except:
                company_name = ticker
                currency = 'USD'

            # Create figure with secondary y-axis
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                subplot_titles=(f'{ticker} Stock Price', 'Volume'),
                row_heights=[0.7, 0.3]
            )

            # Add price line
            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=hist['Close'],
                    name='Close Price',
                    line=dict(color='#0066cc', width=2)
                ),
                row=1, col=1
            )

            # Add volume bars
            fig.add_trace(
                go.Bar(
                    x=hist.index,
                    y=hist['Volume'],
                    name='Volume',
                    marker=dict(color='#7f8c8d')
                ),
                row=2, col=1
            )

            # Update layout
            fig.update_layout(
                title=f'{ticker} - {period.upper()} Performance',
                xaxis_title='',
                yaxis_title=f'Price ({currency})',
                yaxis2_title='Volume',
                hovermode='x unified',
                template='plotly_white',
                height=600,
                showlegend=True,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                )
            )

            # Calculate statistics
            current_price = hist['Close'].iloc[-1]
            start_price = hist['Close'].iloc[0]
            change = current_price - start_price
            change_pct = (change / start_price) * 100
            high_52w = hist['High'].max()
            low_52w = hist['Low'].min()
            avg_volume = hist['Volume'].mean()

            # Format statistics with proper currency symbol
            currency_symbol = {'USD': '$', 'AUD': 'A$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'CAD': 'C$'}.get(currency, currency + ' ')

            stats_md = f"""
### Stock Statistics ({period.upper()})

**Current Price:** {currency_symbol}{current_price:.2f}
**Change:** {currency_symbol}{change:+.2f} ({change_pct:+.2f}%)
**52-Week High:** {currency_symbol}{high_52w:.2f}
**52-Week Low:** {currency_symbol}{low_52w:.2f}
**Avg Volume:** {avg_volume:,.0f}

*Data Source: Yahoo Finance*
*Last Updated: {hist.index[-1].strftime('%Y-%m-%d')}*
            """

            return fig, company_name, stats_md

        except Exception as e:
            return None, "", f"Error fetching data for '{ticker}': {str(e)}"

    def create_interface(self):
        """Create the Gradio interface."""

        with gr.Blocks(
            theme=create_theme(),
            title="Financial Research Agent",
            js="""
            function refresh() {
                const url = new URL(window.location);
                if (url.searchParams.get('__theme') !== 'light') {
                    url.searchParams.set('__theme', 'light');
                    window.location.href = url.href;
                }
            }
            """,
            css="""
                /* ==================== PROFESSIONAL FINANCIAL PLATFORM STYLING ==================== */

                /* Global Container */
                .gradio-container {
                    font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, sans-serif !important;
                    max-width: 1600px;
                    margin: 0 auto;
                    background: #fafbfc;
                }

                /* Clean Card-Based Layout */
                .gr-box, .gr-form, .gr-panel {
                    border-radius: 12px !important;
                    border: 1px solid #e1e4e8 !important;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
                    background: white !important;
                    padding: 20px !important;
                }

                /* Header Typography */
                h1 {
                    font-size: 2.25rem !important;
                    font-weight: 700 !important;
                    color: #0d1117 !important;
                    letter-spacing: -0.02em !important;
                    margin-bottom: 0.5rem !important;
                }

                h2 {
                    font-size: 1.75rem !important;
                    font-weight: 600 !important;
                    color: #1f2937 !important;
                    margin-top: 1.5rem !important;
                    margin-bottom: 1rem !important;
                }

                h3 {
                    font-size: 1.25rem !important;
                    font-weight: 600 !important;
                    color: #374151 !important;
                    margin-top: 1.25rem !important;
                    margin-bottom: 0.75rem !important;
                }

                /* Primary Action Buttons */
                .gr-button-primary {
                    background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%) !important;
                    border: none !important;
                    border-radius: 8px !important;
                    font-weight: 600 !important;
                    font-size: 15px !important;
                    padding: 12px 24px !important;
                    box-shadow: 0 4px 12px rgba(0, 102, 204, 0.2) !important;
                    transition: all 0.2s ease !important;
                    letter-spacing: 0.01em !important;
                }

                .gr-button-primary:hover {
                    background: linear-gradient(135deg, #0052a3 0%, #003d7a 100%) !important;
                    box-shadow: 0 6px 16px rgba(0, 102, 204, 0.3) !important;
                    transform: translateY(-1px) !important;
                }

                /* Secondary Buttons */
                .gr-button-secondary {
                    background: white !important;
                    border: 1.5px solid #d1d5db !important;
                    border-radius: 8px !important;
                    color: #374151 !important;
                    font-weight: 500 !important;
                    transition: all 0.2s ease !important;
                }

                .gr-button-secondary:hover {
                    border-color: #0066cc !important;
                    background: #f8fafc !important;
                    color: #0066cc !important;
                }

                /* Template Buttons */
                .template-button {
                    margin: 6px 4px !important;
                    border-radius: 6px !important;
                    font-size: 14px !important;
                    padding: 8px 16px !important;
                    background: #f3f4f6 !important;
                    border: 1px solid #e5e7eb !important;
                    color: #1f2937 !important;
                    font-weight: 500 !important;
                    transition: all 0.15s ease !important;
                }

                .template-button:hover {
                    background: white !important;
                    border-color: #0066cc !important;
                    color: #0066cc !important;
                    box-shadow: 0 2px 6px rgba(0, 102, 204, 0.1) !important;
                }

                /* Input Fields */
                .query-box textarea,
                input[type="text"],
                .gr-textbox {
                    font-size: 15px !important;
                    border: 1.5px solid #d1d5db !important;
                    border-radius: 8px !important;
                    padding: 12px 16px !important;
                    background: white !important;
                    transition: all 0.2s ease !important;
                }

                .query-box textarea:focus,
                input[type="text"]:focus,
                .gr-textbox:focus {
                    border-color: #0066cc !important;
                    box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1) !important;
                    outline: none !important;
                }

                /* Status Box */
                .status-box {
                    padding: 24px !important;
                    border-radius: 12px !important;
                    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%) !important;
                    border: 1px solid #bae6fd !important;
                    box-shadow: 0 2px 8px rgba(14, 165, 233, 0.08) !important;
                }

                /* Report Content - Professional Reading Experience */
                .report-content {
                    font-family: 'Charter', 'Georgia', 'Times New Roman', serif !important;
                    font-size: 16px !important;
                    line-height: 1.7 !important;
                    color: #1f2937 !important;
                    padding: 24px !important;
                }

                .report-content p {
                    margin-bottom: 1.25em !important;
                }

                .report-content strong {
                    color: #0d1117 !important;
                    font-weight: 600 !important;
                }

                /* Financial Tables - Bloomberg/Morningstar Style */
                .report-content table {
                    border-collapse: collapse !important;
                    width: 100% !important;
                    margin: 24px 0 !important;
                    background: white !important;
                    border-radius: 8px !important;
                    overflow: hidden !important;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
                }

                .report-content table thead {
                    background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
                    border-bottom: 2px solid #0066cc !important;
                }

                .report-content table th {
                    font-weight: 600 !important;
                    font-size: 13px !important;
                    text-transform: uppercase !important;
                    letter-spacing: 0.05em !important;
                    padding: 14px 16px !important;
                    color: #374151 !important;
                    text-align: left !important;
                }

                .report-content table td {
                    padding: 12px 16px !important;
                    border-bottom: 1px solid #f1f5f9 !important;
                    font-size: 15px !important;
                }

                /* Alternate row colors for better readability */
                .report-content table tbody tr:nth-child(even) {
                    background-color: #fafbfc !important;
                }

                .report-content table tbody tr:hover {
                    background-color: #f0f9ff !important;
                    transition: background-color 0.15s ease !important;
                }

                /* Right-align numeric columns */
                .report-content table td:nth-child(2),
                .report-content table td:nth-child(3),
                .report-content table td:nth-child(4),
                .report-content table td:nth-child(5),
                .report-content table th:nth-child(2),
                .report-content table th:nth-child(3),
                .report-content table th:nth-child(4),
                .report-content table th:nth-child(5) {
                    text-align: right !important;
                }

                /* First column (labels) left-aligned */
                .report-content table td:first-child,
                .report-content table th:first-child {
                    text-align: left !important;
                    font-weight: 500 !important;
                }

                /* Monospace font for numbers - professional financial styling */
                .report-content table td:nth-child(n+2) {
                    font-family: 'SF Mono', 'Monaco', 'Menlo', 'Consolas', 'Courier New', monospace !important;
                    font-size: 14px !important;
                    font-variant-numeric: tabular-nums !important;
                }

                /* Source Attribution Badges */
                .report-content code {
                    background: #f3f4f6 !important;
                    border: 1px solid #e5e7eb !important;
                    border-radius: 4px !important;
                    padding: 2px 8px !important;
                    font-size: 13px !important;
                    font-family: 'SF Mono', Monaco, monospace !important;
                    color: #374151 !important;
                }

                /* Enhanced Code Blocks */
                .report-content pre {
                    background: #f8fafc !important;
                    border: 1px solid #e5e7eb !important;
                    border-radius: 8px !important;
                    padding: 16px !important;
                    overflow-x: auto !important;
                    font-size: 14px !important;
                }

                /* Tabs - Force wrapping */
                .tabs {
                    display: flex !important;
                    flex-wrap: wrap !important;
                }

                .tab-nav,
                .tab-nav.svelte-1b6s6s,
                div[role="tablist"] {
                    display: flex !important;
                    flex-wrap: wrap !important;
                    max-width: 100% !important;
                    overflow: visible !important;
                }

                .tab-nav button {
                    font-weight: 500 !important;
                    font-size: 15px !important;
                    padding: 12px 24px !important;
                    flex-shrink: 0 !important;
                    border-radius: 8px 8px 0 0 !important;
                    color: #6b7280 !important;
                    transition: all 0.2s ease !important;
                }

                .tab-nav button.selected {
                    color: #0066cc !important;
                    background: white !important;
                    border-bottom: 2px solid #0066cc !important;
                    font-weight: 600 !important;
                }

                /* Markdown Lists */
                .report-content ul,
                .report-content ol {
                    margin-left: 24px !important;
                    margin-bottom: 1.25em !important;
                }

                .report-content li {
                    margin-bottom: 0.5em !important;
                    line-height: 1.6 !important;
                }

                /* Blockquotes */
                .report-content blockquote {
                    border-left: 4px solid #0066cc !important;
                    padding-left: 20px !important;
                    margin: 20px 0 !important;
                    color: #4b5563 !important;
                    font-style: italic !important;
                    background: #f8fafc !important;
                    padding: 16px 20px !important;
                    border-radius: 0 8px 8px 0 !important;
                }

                /* Horizontal Rules */
                .report-content hr {
                    border: none !important;
                    border-top: 2px solid #e5e7eb !important;
                    margin: 32px 0 !important;
                }

                /* Download Buttons */
                .gr-download-button {
                    background: #10b981 !important;
                    color: white !important;
                    border: none !important;
                    border-radius: 6px !important;
                    font-weight: 500 !important;
                    padding: 8px 16px !important;
                    transition: all 0.2s ease !important;
                }

                .gr-download-button:hover {
                    background: #059669 !important;
                    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2) !important;
                }

                /* Radio Buttons & Dropdowns */
                .gr-radio,
                .gr-dropdown {
                    border-radius: 8px !important;
                }

                /* Progress Bar */
                .progress-bar {
                    background: linear-gradient(90deg, #0066cc, #0ea5e9) !important;
                    border-radius: 8px !important;
                }

                /* Error Messages */
                .error {
                    background: #fef2f2 !important;
                    border: 1px solid #fecaca !important;
                    color: #991b1b !important;
                    padding: 16px !important;
                    border-radius: 8px !important;
                }

                /* Success Messages */
                .success {
                    background: #f0fdf4 !important;
                    border: 1px solid #bbf7d0 !important;
                    color: #166534 !important;
                    padding: 16px !important;
                    border-radius: 8px !important;
                }

                /* Plotly Charts */
                .js-plotly-plot {
                    border-radius: 12px !important;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06) !important;
                }

                /* Footer */
                footer {
                    text-align: center !important;
                    color: #6b7280 !important;
                    font-size: 14px !important;
                    padding: 32px 0 !important;
                }

                /* Mobile Responsiveness */
                @media (max-width: 768px) {
                    .gradio-container {
                        padding: 12px !important;
                    }

                    h1 {
                        font-size: 1.75rem !important;
                    }

                    h2 {
                        font-size: 1.5rem !important;
                    }

                    .report-content {
                        font-size: 15px !important;
                        padding: 16px !important;
                    }

                    .report-content table {
                        font-size: 13px !important;
                    }
                }

                /* ==================== NUMBERED SECTION BADGES ==================== */
                .section-header {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    margin-bottom: 16px !important;
                }

                .section-badge {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: 36px;
                    height: 36px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    font-weight: 600;
                    font-size: 18px;
                    flex-shrink: 0;
                    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
                }

                .section-title {
                    font-size: 1.5rem !important;
                    font-weight: 600 !important;
                    margin: 0 !important;
                    color: #0d1117;
                }

                /* Section containers */
                .home-section {
                    background: white !important;
                    border-radius: 12px !important;
                    padding: 24px !important;
                    margin-bottom: 24px !important;
                    border: 1px solid #e1e4e8 !important;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
                }
            """
        ) as app:

            # Header - Simplified to match Figma design
            gr.Markdown(
                """
                # 📊 AI Financial Analysis Knowledge Base
                Select companies, add new analysis, and query the knowledge base
                """
            )

            # Knowledge Base Status Banner (Summary only)
            kb_status_banner = gr.Markdown(elem_classes=["status-box"])

            # View Details button and expandable details section
            with gr.Row():
                view_details_btn = gr.Button("📋 View Details", size="sm", variant="secondary")

            kb_details_section = gr.Markdown(visible=False, elem_classes=["status-box"])

            # Initialize KB status on load
            def load_kb_status():
                from financial_research_agent.rag.intelligence import get_kb_summary_banner
                from financial_research_agent.rag.chroma_manager import FinancialRAGManager
                from financial_research_agent.config import AgentConfig

                try:
                    rag = FinancialRAGManager(persist_directory=AgentConfig.CHROMA_DB_DIR)
                    return get_kb_summary_banner(rag)
                except Exception as e:
                    return f"### 💾 Knowledge Base Status\n\n*Unable to load: {str(e)}*"

            # Load KB status when app starts
            app.load(fn=load_kb_status, outputs=[kb_status_banner])

            # State to track visibility and content
            details_state = gr.State(value={"visible": False, "content": ""})

            def toggle_with_state(state):
                """Toggle function that uses state instead of component properties"""
                from financial_research_agent.rag.intelligence import get_kb_detailed_status
                from financial_research_agent.rag.chroma_manager import FinancialRAGManager
                from financial_research_agent.config import AgentConfig

                # If currently visible, hide it
                if state["visible"]:
                    return gr.update(visible=False), "📋 View Details", {"visible": False, "content": state["content"]}

                # If currently hidden, show it (load content if not loaded yet)
                try:
                    if not state["content"]:
                        rag = FinancialRAGManager(persist_directory=AgentConfig.CHROMA_DB_DIR)
                        content = get_kb_detailed_status(rag)
                    else:
                        content = state["content"]  # Use cached content

                    return gr.update(value=content, visible=True), "🔼 Hide Details", {"visible": True, "content": content}
                except Exception as e:
                    return gr.update(value=f"*Unable to load details: {str(e)}*", visible=True), "🔼 Hide Details", {"visible": True, "content": ""}

            # Toggle details when button clicked
            view_details_btn.click(
                fn=toggle_with_state,
                inputs=[details_state],
                outputs=[kb_details_section, view_details_btn, details_state]
            )

            with gr.Tabs() as main_tabs:

                # ==================== TAB 1: HOME ====================
                with gr.Tab("🏠 Home", id=0) as home_tab:

                    # ==================== SECTION 1: View Existing Analysis ====================
                    with gr.Group(elem_classes=["home-section"]):
                        gr.HTML("""
                            <div class="section-header">
                                <div class="section-badge">1</div>
                                <h2 class="section-title">View Existing Analysis</h2>
                            </div>
                        """)
                        gr.Markdown("*Load a previously generated financial analysis report from your history*")

                        with gr.Row():
                            existing_dropdown = gr.Dropdown(
                                label="Select Previous Analysis",
                                choices=[],
                                interactive=True,
                                scale=3
                            )
                            refresh_btn = gr.Button("🔄 Refresh List", size="sm", scale=1)

                        load_btn = gr.Button("📂 Load Analysis", variant="primary", size="lg")

                    # ==================== SECTION 2: Run New Analysis ====================
                    with gr.Group(elem_classes=["home-section"]):
                        gr.HTML("""
                            <div class="section-header">
                                <div class="section-badge">2</div>
                                <h2 class="section-title">Run New Analysis</h2>
                            </div>
                        """)
                        gr.Markdown("*Generate a comprehensive financial research report for any public company (takes 5-10 minutes)*")

                        query_input = gr.Textbox(
                            label="Company Ticker or Name",
                            placeholder="E.g., 'AAPL' or 'Apple' or 'Analyze Tesla's Q3 2025 performance'",
                            lines=2,
                            elem_classes=["query-box"]
                        )

                        generate_btn = gr.Button(
                            "🔍 Generate Analysis",
                            variant="primary",
                            size="lg"
                        )

                        status_output = gr.Markdown(
                            label="Status",
                            elem_classes=["status-box"]
                        )

                    # ==================== SECTION 3: Query Knowledge Base ====================
                    with gr.Group(elem_classes=["home-section"]):
                        gr.HTML("""
                            <div class="section-header">
                                <div class="section-badge">3</div>
                                <h2 class="section-title">Query Knowledge Base</h2>
                            </div>
                        """)
                        gr.Markdown("*Ask questions about any company already analyzed and get AI-powered answers with citations*")

                        kb_query_input = gr.Textbox(
                            label="Search Query",
                            placeholder="E.g., 'What are Apple's main revenue sources?'",
                            lines=2
                        )

                        gr.Markdown("#### Example Questions")
                        gr.Markdown("*Click an example to auto-fill the search*")

                        with gr.Row():
                            with gr.Column(scale=1):
                                for example in KB_QUERY_EXAMPLES[:3]:
                                    btn = gr.Button(
                                        example,
                                        size="sm",
                                        elem_classes=["template-button"]
                                    )
                                    btn.click(
                                        fn=lambda ex=example: ex,
                                        outputs=kb_query_input
                                    )

                            with gr.Column(scale=1):
                                for example in KB_QUERY_EXAMPLES[3:]:
                                    btn = gr.Button(
                                        example,
                                        size="sm",
                                        elem_classes=["template-button"]
                                    )
                                    btn.click(
                                        fn=lambda ex=example: ex,
                                        outputs=kb_query_input
                                    )

                        kb_search_btn = gr.Button("🔍 Search Knowledge Base", variant="primary", size="lg")

                        kb_results_output = gr.Markdown(
                            label="Search Results",
                            value="*Enter a query and click Search to find relevant information*"
                        )

                # ==================== REPORTS TAB (PARENT) ====================
                with gr.Tab("📊 Reports"):
                    with gr.Tabs():

                        # ==================== TAB 2: Comprehensive Report ====================
                        with gr.Tab("📄 Summary", id=1):
                            gr.Markdown(
                                """
                                ## Full Investment-Grade Research Report
                                *3-5 page comprehensive analysis including executive summary,
                                financial performance, risk assessment, and forward-looking indicators*
                                """
                            )

                            comprehensive_output = gr.Markdown(
                                label="Research Report",
                                elem_classes=["report-content"]
                            )

                            with gr.Row():
                                download_comp_md = gr.DownloadButton(
                                    label="📥 Download as Markdown",
                                    visible=False
                                )
                                # download_comp_md = gr.Button(
                                #     "📥 Download as PDF",
                                #     size="sm"
                                # )

                        # ==================== TAB 3: Financial Statements ====================
                        with gr.Tab("💰 Financial Statements", id=2):
                            gr.Markdown(
                                """
                                ## Complete Financial Statements from SEC EDGAR
                                *Balance Sheet, Income Statement, and Cash Flow Statement
                                with comparative periods and human-readable labels*
                                """
                            )

                            with gr.Tabs():
                                with gr.Tab("All Statements"):
                                    statements_output = gr.Markdown(
                                        elem_classes=["report-content"]
                                    )

                                # Future: Individual statement tabs with interactive tables
                                # with gr.Tab("Balance Sheet"):
                                #     balance_sheet_table = gr.DataFrame()
                                # with gr.Tab("Income Statement"):
                                #     income_statement_table = gr.DataFrame()
                                # with gr.Tab("Cash Flow"):
                                #     cash_flow_table = gr.DataFrame()

                            with gr.Row():
                                download_stmt_md = gr.DownloadButton(
                                    label="📥 Download Statements",
                                    visible=False
                                )

                        # ==================== TAB 4: Financial Metrics ====================
                        with gr.Tab("📈 Metrics", id=3):
                            gr.Markdown(
                                """
                                ## Financial Metrics Analysis with YoY Comparison
                                *Liquidity, Solvency, Profitability, and Efficiency ratios
                                with comparative period analysis and trend indicators*
                                """
                            )

                            metrics_output = gr.Markdown(
                                elem_classes=["report-content"]
                            )

                            with gr.Row():
                                download_metrics_md = gr.DownloadButton(
                                    label="📥 Download Metrics",
                                    visible=False
                                )

                        # ==================== TAB 4.5: Banking Ratios (Conditional) ====================
                        with gr.Tab("🏦 Banking Ratios", id=8, visible=False) as banking_ratios_tab:
                            gr.Markdown(
                                """
                                ## Banking Regulatory Ratios Analysis
                                *Basel III capital ratios, liquidity metrics, and banking-specific ratios
                                for commercial banks and financial institutions*

                                **Includes:**
                                - **TIER 1 Ratios (Directly Reported):** CET1, Tier 1 Capital, Total Capital, Leverage, LCR, NSFR
                                - **TIER 2 Ratios (Calculated):** NIM, Efficiency Ratio, ROTCE, NPL Ratio, Loan-to-Deposit

                                *This tab only appears for banking sector companies (commercial banks, G-SIBs, regional banks)*
                                """
                            )

                            banking_ratios_output = gr.Markdown(
                                elem_classes=["report-content"]
                            )

                            with gr.Row():
                                download_banking_md = gr.DownloadButton(
                                    label="📥 Download Banking Ratios",
                                    visible=False
                                )

                        # ==================== TAB 5: Financial Analysis ====================
                        with gr.Tab("💡 Analysis", id=4):
                            gr.Markdown(
                                """
                                ## Specialist Financial Analysis
                                *In-depth analysis of financial performance, trends, and key metrics
                                by the Financial Analyst agent with direct access to SEC EDGAR data*
                                """
                            )

                            financial_analysis_output = gr.Markdown(
                                elem_classes=["report-content"]
                            )

                            # Interactive Charts Section
                            gr.Markdown("### 📊 Interactive Charts")

                            with gr.Row():
                                margin_chart = gr.Plot(
                                    label="Revenue & Profitability Trends",
                                    visible=True
                                )
                                metrics_chart = gr.Plot(
                                    label="Margin Trends",
                                    visible=True
                                )

                            with gr.Row():
                                segment_chart = gr.Plot(
                                    label="Revenue by Segment",
                                    visible=True
                                )

                            with gr.Row():
                                download_fin_analysis_md = gr.DownloadButton(
                                    label="📥 Download Financial Analysis",
                                    visible=False
                                )

                        # ==================== TAB 6: Risk Analysis ====================
                        with gr.Tab("⚠️ Risks", id=5):
                            gr.Markdown(
                                """
                                ## Specialist Risk Assessment
                                *Comprehensive risk analysis prioritizing 10-K Item 1A Risk Factors
                                by the Risk Analyst agent with access to annual and quarterly SEC filings*
                                """
                            )

                            risk_analysis_output = gr.Markdown(
                                elem_classes=["report-content"]
                            )

                            with gr.Row():
                                risk_chart = gr.Plot(
                                    label="Balance Sheet Composition",
                                    visible=True
                                )

                            with gr.Row():
                                download_risk_analysis_md = gr.DownloadButton(
                                    label="📥 Download Risk Analysis",
                                    visible=False
                                )

                        # ==================== TAB 7: Data Verification ====================
                        with gr.Tab("✅ Checks", id=6):
                            gr.Markdown(
                                """
                                ## Data Quality & Validation Report
                                *Verification of data completeness, balance sheet equations,
                                comparative periods, and critical line items*
                                """
                            )

                            verification_output = gr.Markdown(
                                elem_classes=["report-content"]
                            )

                            gr.Markdown(
                                """
                                ---

                                **Data Source:** All financial data is extracted directly from official
                                SEC EDGAR filings using XBRL precision. Values are exact to the penny
                                as reported in SEC filings.

                                **Methodology:** Deterministic extraction using edgartools library,
                                validated against balance sheet equations and completeness checks.
                                """
                            )

                        # ==================== TAB 8: Cost Report ====================
                        with gr.Tab("💰 Cost Report", id=8):
                            gr.Markdown(
                                """
                                ## Analysis Cost Breakdown
                                *Detailed token usage and costs per agent*

                                This report shows the exact cost breakdown for generating this analysis,
                                including per-agent token usage and API costs.
                                """
                            )

                            cost_report_output = gr.Markdown(
                                elem_classes=["report-content"]
                            )

                        # ==================== TAB 9: Search Results (Dev) ====================
                        with gr.Tab("🔍 Search Results", id=9):
                            gr.Markdown(
                                """
                                ## Multi-Source Search Results
                                *Combined search results from web and various data sources
                                used in generating the analysis*

                                **Note:** This tab is primarily for development and debugging purposes.
                                """
                            )

                            search_results_output = gr.Markdown(
                                elem_classes=["report-content"]
                            )

                        # ==================== TAB 10: Stock Price ====================
                        with gr.Tab("📈 Stock Price", id=10):
                            gr.Markdown(
                                """
                                ## Live Stock Price Charts
                                *Real-time stock price data from Yahoo Finance*

                                Enter a ticker symbol to view interactive price charts and key statistics.
                                Data is fetched on-demand and not stored in the knowledge base.
                                """
                            )

                            with gr.Row():
                                with gr.Column(scale=3):
                                    stock_ticker_input = gr.Textbox(
                                        label="Ticker Symbol",
                                        placeholder="e.g., AAPL, MSFT, GOOGL, WBC.AX",
                                        value=""
                                    )
                                with gr.Column(scale=2):
                                    stock_period_dropdown = gr.Dropdown(
                                        label="Time Period",
                                        choices=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
                                        value="1y"
                                    )
                                with gr.Column(scale=1):
                                    fetch_stock_btn = gr.Button(
                                        "📊 Fetch Chart",
                                        variant="primary"
                                    )

                            # Company name display
                            stock_company_name = gr.Markdown(
                                visible=False,
                                elem_classes=["report-content"]
                            )

                            stock_chart_output = gr.Plot(
                                label="Stock Price Chart",
                                visible=True
                            )

                            stock_stats_output = gr.Markdown(
                                elem_classes=["report-content"]
                            )

                        # ==================== TAB 11: EDGAR Filings (Dev) ====================
                        with gr.Tab("📄 EDGAR Filings", id=11):
                            gr.Markdown(
                                """
                                ## SEC EDGAR Filings Data
                                *Raw EDGAR filings information and metadata extracted
                                from SEC database*

                                **Note:** This tab is primarily for development and debugging purposes.
                                """
                            )

                            edgar_filings_output = gr.Markdown(
                                elem_classes=["report-content"]
                            )

            # Footer
            gr.Markdown(
                """
                ---

                **About:** This tool generates investment-grade financial analysis reports using
                official SEC EDGAR filings. All data is extracted with XBRL precision and validated
                for accuracy and completeness.

                **Disclaimer:** This tool is for informational and educational purposes only.
                Not financial advice. Always consult with qualified financial professionals
                before making investment decisions.
                """
            )

            # Connect the generate button to the analysis function
            generate_btn.click(
                fn=self.generate_analysis,
                inputs=[query_input],
                outputs=[
                    status_output,
                    comprehensive_output,
                    statements_output,
                    metrics_output,
                    banking_ratios_output,  # NEW: Banking ratios
                    financial_analysis_output,
                    risk_analysis_output,
                    verification_output,
                    cost_report_output,  # NEW: Cost report
                    search_results_output,
                    edgar_filings_output,
                    margin_chart,
                    metrics_chart,
                    risk_chart,
                    banking_ratios_tab  # NEW: Tab visibility
                ]
            )


            # Refresh button for existing analyses dropdown
            refresh_btn.click(
                fn=self.refresh_dropdown_choices,
                outputs=[existing_dropdown]
            )

            # Load button for existing analyses
            load_btn.click(
                fn=self.load_existing_analysis,
                inputs=[existing_dropdown],
                outputs=[
                    status_output,
                    comprehensive_output,
                    statements_output,
                    metrics_output,
                    banking_ratios_output,  # NEW: Banking ratios
                    financial_analysis_output,
                    risk_analysis_output,
                    verification_output,
                    cost_report_output,  # NEW: Cost report
                    search_results_output,
                    edgar_filings_output,
                    margin_chart,
                    metrics_chart,
                    risk_chart,
                    banking_ratios_tab  # NEW: Tab visibility
                ]
            )

            # Knowledge base search button - using defaults for removed filters
            # Note: query_knowledge_base is a generator, so we need to consume it
            def kb_search_handler(query, progress=gr.Progress()):
                """Wrapper to consume the generator and return final result with progress tracking."""
                try:
                    result_parts = []

                    # Map progress messages to completion percentages
                    progress_map = {
                        "🔍 Analyzing query...": (0.25, "Analyzing query"),
                        "🔍 Searching knowledge base...": (0.50, "Searching knowledge base"),
                        "🤖 Querying each company separately for balanced comparison...": (0.60, "Querying companies"),
                        "🤖 Synthesizing answer from sources...": (0.75, "Synthesizing answer"),
                    }

                    for chunk in self.query_knowledge_base(query, "", "", 10):
                        result_parts.append(chunk)

                        # Update progress if this is a known progress message
                        if chunk in progress_map:
                            pct, desc = progress_map[chunk]
                            progress(pct, desc=desc)

                    # Mark as complete
                    progress(1.0, desc="Complete")

                    # Return the last (final) result which contains the complete output
                    return result_parts[-1] if result_parts else "No results"
                except Exception as e:
                    import traceback
                    error_detail = traceback.format_exc()
                    return f"### ❌ Error\n\nFailed to query knowledge base:\n\n```\n{str(e)}\n```\n\n<details>\n<summary>Full Error Details</summary>\n\n```\n{error_detail}\n```\n</details>"

            kb_search_btn.click(
                fn=kb_search_handler,
                inputs=[kb_query_input],
                outputs=[kb_results_output]
            )

            # Stock chart fetch button - wrapper to format company name output
            def fetch_and_format(ticker, period):
                fig, company_name, stats = self.fetch_stock_price_chart(ticker, period)
                # Format company name for display
                if company_name:
                    company_display = gr.update(value=f"### {company_name}", visible=True)
                else:
                    company_display = gr.update(value="", visible=False)
                return fig, company_display, stats

            fetch_stock_btn.click(
                fn=fetch_and_format,
                inputs=[stock_ticker_input, stock_period_dropdown],
                outputs=[stock_chart_output, stock_company_name, stock_stats_output]
            )


            # Populate dropdown on app load
            def load_dropdown_choices():
                analyses = self.get_existing_analyses()
                choices = [a['label'] for a in analyses]
                # Store mapping for later retrieval
                self.analysis_map = {a['label']: a['value'] for a in analyses}
                return gr.update(choices=choices, value=choices[0] if choices else None)

            # Auto-populate dropdown on app load
            # Re-enabled after fixing persistent storage (was disabled for Modal/Railway performance)
            # Now that /data/output works correctly, startup scan is fast
            app.load(
                fn=load_dropdown_choices,
                outputs=[existing_dropdown]
            )

            # TODO: Pre-populate stock ticker from Home page query
            # Feature temporarily disabled - requires different approach for tab selection events
            # The .select() event doesn't provide tab index, need to investigate alternative

        return app

    def launch(self, **kwargs):
        """Launch the Gradio app."""
        app = self.create_interface()

        # Default launch settings
        launch_settings = {
            'server_name': '0.0.0.0',
            'server_port': 7860,
            'share': False,
            'show_error': True,
            'inbrowser': True,  # Auto-open browser
            'favicon_path': None,
        }
        launch_settings.update(kwargs)

        app.launch(**launch_settings)


def main():
    """Main entry point for web app."""
    web_app = WebApp()
    web_app.launch()


if __name__ == "__main__":
    main()
