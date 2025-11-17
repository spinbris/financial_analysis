"""
ChromaDB manager for financial analysis RAG.

Handles indexing, querying, and managing financial analysis documents.
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
from datetime import datetime
from typing import Any
import re


class FinancialRAGManager:
    """Manages ChromaDB for financial analysis RAG."""

    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize ChromaDB client.

        Args:
            persist_directory: Directory for ChromaDB persistence
        """
        self.persist_directory = persist_directory
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection with OpenAI embeddings
        self.collection = self.client.get_or_create_collection(
            name="financial_analyses",
            metadata={"hnsw:space": "cosine"}
        )

    def index_analysis_from_directory(
        self,
        output_dir: str | Path,
        ticker: str
    ) -> dict[str, Any]:
        """
        Parse and index all markdown analyses from an output directory.

        Args:
            output_dir: Path to analysis output directory
            ticker: Stock ticker symbol

        Returns:
            Metadata about indexing operation
        """
        output_dir = Path(output_dir)

        if not output_dir.exists():
            raise FileNotFoundError(f"Output directory not found: {output_dir}")

        # Map of analysis types to filenames (updated to match actual output)
        analysis_files = {
            "comprehensive": "07_comprehensive_report.md",
            "financial_statements": "03_financial_statements.md",
            "financial_metrics": "04_financial_metrics.md",
            "financial_analysis": "05_financial_analysis.md",
            "risk": "06_risk_analysis.md"
        }

        total_chunks = 0
        indexed_files = []

        for analysis_type, filename in analysis_files.items():
            filepath = output_dir / filename

            if not filepath.exists():
                print(f"⚠️  Skipping {filename} (not found)")
                continue

            # Read markdown content
            content = filepath.read_text(encoding="utf-8")

            # Extract metadata from content
            metadata = self._extract_metadata(content, ticker, analysis_type)

            # Chunk the content
            chunks = self._chunk_markdown(content, analysis_type, metadata)

            if chunks:
                # Use upsert to handle duplicates (will update if ID exists, insert if new)
                # This allows re-indexing the same ticker without creating duplicates
                self.collection.upsert(
                    documents=[chunk["text"] for chunk in chunks],
                    metadatas=[chunk["metadata"] for chunk in chunks],
                    ids=[chunk["id"] for chunk in chunks]
                )

                total_chunks += len(chunks)
                indexed_files.append(filename)
                print(f"✓ Indexed {filename}: {len(chunks)} chunks")

        return {
            "ticker": ticker,
            "total_chunks": total_chunks,
            "indexed_files": indexed_files,
            "output_dir": str(output_dir),
            "indexed_at": datetime.now().isoformat()
        }

    def _extract_metadata(
        self,
        content: str,
        ticker: str,
        analysis_type: str
    ) -> dict[str, str]:
        """
        Extract metadata from markdown content.

        Args:
            content: Markdown content
            ticker: Stock ticker
            analysis_type: Type of analysis

        Returns:
            Metadata dictionary with source attribution
        """
        metadata = {
            "ticker": ticker.upper(),
            "analysis_type": analysis_type,
            # Source attribution (3-tier system)
            "source_tier": "core",  # core | enhanced | supplemental
            "data_source": "SEC",   # SEC-10K | SEC-10Q | web-search
            "validation_status": "validated",  # validated | unverified
            "enhancement_type": "none"  # none | chart | graph | summary | web-context
        }

        # Extract company name
        company_match = re.search(r'\*\*Company:\*\*\s+(.+?)(?:\s*\n|\s*$)', content)
        if company_match:
            metadata["company"] = company_match.group(1).strip()

        # Extract period
        period_match = re.search(r'\*\*Period:\*\*\s+(.+?)(?:\s*\n|\s*$)', content)
        if period_match:
            metadata["period"] = period_match.group(1).strip()

        # Extract filing reference
        filing_match = re.search(r'\*\*Filing:\*\*\s+(.+?)(?:\s*\n|\s*$)', content)
        if filing_match:
            metadata["filing"] = filing_match.group(1).strip()
            # Determine specific SEC filing type from filing reference
            if "10-K" in metadata["filing"]:
                metadata["data_source"] = "SEC-10K"
            elif "10-Q" in metadata["filing"]:
                metadata["data_source"] = "SEC-10Q"

        return metadata

    def _chunk_markdown(
        self,
        content: str,
        analysis_type: str,
        metadata: dict[str, str],
        chunk_size: int = 2000,
        overlap: int = 200
    ) -> list[dict]:
        """
        Chunk markdown content by sections while preserving formatting.

        Args:
            content: Markdown content
            analysis_type: Type of analysis
            metadata: Base metadata
            chunk_size: Target characters per chunk (increased for better context)
            overlap: Overlap characters between chunks

        Returns:
            List of chunk dictionaries with text, metadata, and IDs
        """
        chunks = []

        # Split by sections (###)
        sections = re.split(r'\n### ', content)

        for i, section in enumerate(sections):
            if not section.strip():
                continue

            # Extract section title
            lines = section.split('\n', 1)
            section_title = lines[0].strip('#').strip() if lines else "Introduction"
            section_content = lines[1] if len(lines) > 1 else ""

            if not section_content.strip():
                continue

            # CHARACTER-based chunking to preserve markdown formatting
            # Split on paragraph boundaries (double newline) when possible
            paragraphs = section_content.split('\n\n')

            current_chunk = []
            current_size = 0
            chunk_num = 0

            for para in paragraphs:
                para_size = len(para)

                # If adding this paragraph exceeds chunk size and we already have content
                if current_size + para_size > chunk_size and current_chunk:
                    # Save current chunk
                    chunk_text = '\n\n'.join(current_chunk)
                    chunk_metadata = {
                        **metadata,
                        "section": section_title,
                        "chunk_num": chunk_num,
                        "section_num": i
                    }
                    chunk_id = f"{metadata['ticker']}_{analysis_type}_s{i}_c{chunk_num}_{datetime.now().strftime('%Y%m%d')}"

                    chunks.append({
                        "text": f"### {section_title}\n\n{chunk_text}",
                        "metadata": chunk_metadata,
                        "id": chunk_id
                    })

                    # Start new chunk with overlap (keep last paragraph for context)
                    if len(current_chunk) > 1:
                        current_chunk = [current_chunk[-1], para]
                        current_size = len(current_chunk[-2]) + para_size + 2  # +2 for \n\n
                    else:
                        current_chunk = [para]
                        current_size = para_size

                    chunk_num += 1
                else:
                    # Add paragraph to current chunk
                    current_chunk.append(para)
                    current_size += para_size + 2  # +2 for \n\n separator

            # Save final chunk if it has content
            if current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                chunk_metadata = {
                    **metadata,
                    "section": section_title,
                    "chunk_num": chunk_num,
                    "section_num": i
                }
                chunk_id = f"{metadata['ticker']}_{analysis_type}_s{i}_c{chunk_num}_{datetime.now().strftime('%Y%m%d')}"

                chunks.append({
                    "text": f"### {section_title}\n\n{chunk_text}",
                    "metadata": chunk_metadata,
                    "id": chunk_id
                })

        return chunks

    def query(
        self,
        query: str,
        ticker: str | None = None,
        analysis_type: str | None = None,
        n_results: int = 5
    ) -> dict[str, Any]:
        """
        Query ChromaDB for relevant analysis chunks.

        Args:
            query: Natural language query
            ticker: Optional ticker filter
            analysis_type: Optional analysis type filter
            n_results: Number of results to return

        Returns:
            Query results with documents, metadatas, and distances
        """
        # Build where filter - use $and when multiple conditions
        where_filter = None
        if ticker and analysis_type:
            # Multiple conditions - use $and operator
            where_filter = {
                "$and": [
                    {"ticker": ticker.upper()},
                    {"analysis_type": analysis_type}
                ]
            }
        elif ticker:
            where_filter = {"ticker": ticker.upper()}
        elif analysis_type:
            where_filter = {"analysis_type": analysis_type}

        # Query ChromaDB
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter
        )

        return results

    def query_with_synthesis(
        self,
        query: str,
        ticker: str | None = None,
        analysis_type: str | None = None,
        n_results: int = 5
    ) -> 'RAGResponse':
        """
        Query ChromaDB and synthesize results into a coherent answer.

        This is the recommended method for user-facing Q&A, as it:
        - Retrieves relevant chunks via semantic search
        - Synthesizes them into a cohesive, well-cited answer
        - Provides confidence assessment and limitations

        Args:
            query: Natural language query
            ticker: Optional ticker filter
            analysis_type: Optional analysis type filter
            n_results: Number of results to retrieve (default: 5)

        Returns:
            RAGResponse with synthesized answer, sources, confidence, and limitations

        Example:
            >>> rag_manager = FinancialRAGManager()
            >>> response = rag_manager.query_with_synthesis(
            ...     "What were Apple's Q3 revenues?",
            ...     ticker="AAPL"
            ... )
            >>> print(response.answer)
            >>> print(f"Confidence: {response.confidence}")
            >>> print(f"Sources: {', '.join(response.sources_cited)}")
        """
        from .synthesis_agent import synthesize_rag_results

        # Get raw search results from ChromaDB
        search_results = self.query(
            query=query,
            ticker=ticker,
            analysis_type=analysis_type,
            n_results=n_results
        )

        # Synthesize into coherent response
        response = synthesize_rag_results(query, search_results)

        return response

    def compare_peers(
        self,
        tickers: list[str],
        query: str,
        n_results_per_company: int = 3
    ) -> dict[str, Any]:
        """
        Compare multiple companies on a specific aspect.

        Args:
            tickers: List of ticker symbols
            query: Comparison query
            n_results_per_company: Results per company

        Returns:
            Dictionary mapping tickers to their results
        """
        comparison = {}

        for ticker in tickers:
            results = self.query(
                query=query,
                ticker=ticker,
                n_results=n_results_per_company
            )
            comparison[ticker] = results

        return comparison

    def list_companies(self) -> list[dict[str, str]]:
        """
        List all companies with analyses in ChromaDB.

        Returns:
            List of company metadata dictionaries
        """
        # Get all documents (limit to metadata only)
        all_docs = self.collection.get()

        # Extract unique companies
        companies = {}
        for metadata in all_docs["metadatas"]:
            ticker = metadata.get("ticker")
            if ticker and ticker not in companies:
                companies[ticker] = {
                    "ticker": ticker,
                    "company": metadata.get("company", ""),
                    "latest_period": metadata.get("period", ""),
                    "filing_type": metadata.get("filing", "").split()[0] if metadata.get("filing") else ""
                }

        return list(companies.values())

    def get_latest_analysis(self, ticker: str) -> dict[str, Any] | None:
        """
        Get the latest analysis for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Analysis metadata or None if not found
        """
        results = self.collection.get(
            where={"ticker": ticker.upper()},
            limit=1
        )

        if not results["metadatas"]:
            return None

        metadata = results["metadatas"][0]

        # Extract date from chunk_id (format: TICKER_type_s0_c0_YYYYMMDD)
        chunk_id = results.get("ids", [[]])[0][0] if results.get("ids") else ""
        date_match = re.search(r'_(\d{8})$', chunk_id)

        if date_match:
            date_str = date_match.group(1)
            analysis_date = datetime.strptime(date_str, "%Y%m%d")
            days_old = (datetime.now() - analysis_date).days
        else:
            days_old = 999  # Unknown age

        return {
            "ticker": ticker,
            "analysis_date": metadata.get("period", "Unknown"),
            "days_old": days_old
        }

    def get_companies_with_status(self) -> list[dict]:
        """
        Get all indexed companies with status metadata.

        Returns:
            [
                {
                    "ticker": "AAPL",
                    "company": "Apple Inc.",
                    "period": "Q3 FY2024",
                    "filing": "10-Q",
                    "days_old": 2,
                    "status": "fresh",  # "fresh" | "aging" | "stale"
                    "last_updated": "2025-11-06"
                },
                ...
            ]
        """
        all_docs = self.collection.get()

        companies_map = {}
        for i, metadata in enumerate(all_docs["metadatas"]):
            ticker = metadata.get("ticker")
            if not ticker or ticker in companies_map:
                continue

            # Extract date from chunk_id (format: TICKER_type_s0_c0_YYYYMMDD)
            chunk_id = all_docs["ids"][i] if i < len(all_docs["ids"]) else ""
            date_match = re.search(r'_(\d{8})$', chunk_id)

            if date_match:
                date_str = date_match.group(1)
                analysis_date = datetime.strptime(date_str, "%Y%m%d")
                days_old = (datetime.now() - analysis_date).days
                last_updated = analysis_date.strftime("%Y-%m-%d")
            else:
                days_old = 999  # Unknown age
                last_updated = "Unknown"

            companies_map[ticker] = {
                "ticker": ticker,
                "company": metadata.get("company", ""),
                "period": metadata.get("period", ""),
                "filing": metadata.get("filing", "").split()[0] if metadata.get("filing") else "",
                "days_old": days_old,
                "status": self._get_staleness_status(days_old, ticker),
                "last_updated": last_updated
            }

        return sorted(companies_map.values(), key=lambda x: x["days_old"])

    def check_company_status(self, ticker: str) -> dict:
        """
        Check if a specific company is in KB and its status.

        Args:
            ticker: Stock ticker symbol

        Returns:
            {
                "in_kb": bool,
                "ticker": str,
                "status": "missing" | "fresh" | "aging" | "stale",
                "days_old": int | None,
                "metadata": dict | None
            }
        """
        all_companies = self.get_companies_with_status()

        for company in all_companies:
            if company["ticker"] == ticker.upper():
                return {
                    "in_kb": True,
                    "ticker": ticker.upper(),
                    "status": company["status"],
                    "days_old": company["days_old"],
                    "metadata": company
                }

        # Not found
        return {
            "in_kb": False,
            "ticker": ticker.upper(),
            "status": "missing",
            "days_old": None,
            "metadata": None
        }

    def _get_staleness_status(self, days_old: int, ticker: str) -> str:
        """
        Determine staleness status based on age and ticker volatility.

        Args:
            days_old: Days since analysis
            ticker: Stock ticker

        Returns:
            "fresh" | "aging" | "stale"
        """
        # High-volatility tickers (simplified - can be enhanced with actual volatility data)
        high_volatility = ticker.upper() in ["TSLA", "NVDA", "AMD", "PLTR", "RIVN", "LCID"]

        if high_volatility:
            if days_old <= 7:
                return "fresh"
            elif days_old <= 30:
                return "aging"
            else:
                return "stale"
        else:
            # Stable blue chips
            if days_old <= 30:
                return "fresh"
            elif days_old <= 90:
                return "aging"
            else:
                return "stale"

    def reset(self):
        """Reset/clear the entire collection (use with caution)."""
        self.client.delete_collection("financial_analyses")
        self.collection = self.client.get_or_create_collection(
            name="financial_analyses",
            metadata={"hnsw:space": "cosine"}
        )
