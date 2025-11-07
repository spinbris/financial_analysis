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
            Metadata dictionary
        """
        metadata = {
            "ticker": ticker.upper(),
            "analysis_type": analysis_type
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

        return metadata

    def _chunk_markdown(
        self,
        content: str,
        analysis_type: str,
        metadata: dict[str, str],
        chunk_size: int = 300,
        overlap: int = 50
    ) -> list[dict]:
        """
        Chunk markdown content by sections for better retrieval.

        Args:
            content: Markdown content
            analysis_type: Type of analysis
            metadata: Base metadata
            chunk_size: Target tokens per chunk
            overlap: Overlap tokens between chunks

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

            # Simple word-based chunking (approximate token count)
            words = section_content.split()

            if not words:
                continue

            # Create overlapping chunks
            start = 0
            chunk_num = 0

            while start < len(words):
                end = start + chunk_size
                chunk_words = words[start:end]
                chunk_text = ' '.join(chunk_words)

                # Create chunk metadata
                chunk_metadata = {
                    **metadata,
                    "section": section_title,
                    "chunk_num": chunk_num,
                    "section_num": i
                }

                # Create unique ID
                chunk_id = f"{metadata['ticker']}_{analysis_type}_s{i}_c{chunk_num}_{datetime.now().strftime('%Y%m%d')}"

                chunks.append({
                    "text": f"### {section_title}\n\n{chunk_text}",
                    "metadata": chunk_metadata,
                    "id": chunk_id
                })

                # Move to next chunk with overlap
                start += (chunk_size - overlap)
                chunk_num += 1

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
        # Build where filter
        where_filter = {}
        if ticker:
            where_filter["ticker"] = ticker.upper()
        if analysis_type:
            where_filter["analysis_type"] = analysis_type

        # Query ChromaDB
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter if where_filter else None
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

        # Calculate days since analysis
        # (simplified - would need to parse actual date from metadata)
        days_old = 999  # Placeholder

        return {
            "ticker": ticker,
            "analysis_date": metadata.get("period", "Unknown"),
            "days_old": days_old
        }

    def reset(self):
        """Reset/clear the entire collection (use with caution)."""
        self.client.delete_collection("financial_analyses")
        self.collection = self.client.get_or_create_collection(
            name="financial_analyses",
            metadata={"hnsw:space": "cosine"}
        )
