/**
 * API Integration for SJP Financial Analysis
 * 
 * This file provides typed API calls to the FastAPI backend.
 * Replace the mock data in your components with these functions.
 * 
 * @module api/integration
 */

// ============================================================================
// Configuration
// ============================================================================

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000');

// ============================================================================
// TypeScript Interfaces
// ============================================================================

export interface QueryRequest {
  query: string;
  ticker?: string;
  n_results?: number;
  analysis_type?: string;
}

export interface Source {
  ticker: string;
  type: string;
  content: string;
  distance: number;
  timestamp?: string;
}

export interface QueryResponse {
  query: string;
  answer: string;
  sources: Source[];
  confidence: 'high' | 'medium' | 'low';
  suggestions: string[];
}

export interface AnalysisRequest {
  ticker: string;
  query?: string;
  force_refresh?: boolean;
}

export interface AnalysisStatus {
  status: 'queued' | 'running' | 'completed' | 'failed';
  ticker: string;
  message: string;
  progress?: number;
  output_dir?: string;
  error?: string;
}

export interface Company {
  name: string;
  ticker: string;
  last_updated?: string;
  analysis_count: number;
}

export interface CompareRequest {
  tickers: string[];
  query: string;
  n_results_per_company?: number;
}

export interface Report {
  ticker: string;
  company_name: string;
  timestamp: string;
  analyses: {
    financial_statements: any[];
    financial_metrics: any[];
    risk_analysis: any[];
    comprehensive_report: any[];
    other: any[];
  };
}

export interface HealthResponse {
  status: string;
  version: string;
  rag_enabled: boolean;
  timestamp: string;
}

// ============================================================================
// Error Handling
// ============================================================================

export class APIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

// ============================================================================
// Core Fetch Function
// ============================================================================

async function fetchWithTimeout(
  url: string,
  options: RequestInit = {}
): Promise<any> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: `HTTP ${response.status}: ${response.statusText}`,
      }));

      throw new APIError(
        error.detail || error.message || 'Request failed',
        response.status,
        error
      );
    }

    return response.json();
  } catch (error: any) {
    clearTimeout(timeoutId);

    if (error.name === 'AbortError') {
      throw new APIError(
        'Request timeout - the server took too long to respond. ' +
        'Analysis may still be running in the background.',
        408
      );
    }

    if (error instanceof APIError) {
      throw error;
    }

    throw new APIError(
      error.message || 'Network error occurred',
      0,
      error
    );
  }
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Check API health status
 */
export async function checkHealth(): Promise<HealthResponse> {
  return await fetchWithTimeout(`${API_BASE_URL}/api/health`);
}

/**
 * Get list of all companies in the knowledge base
 */
export async function getCompanies(): Promise<Company[]> {
  return await fetchWithTimeout(`${API_BASE_URL}/api/companies`);
}

/**
 * Query the knowledge base with semantic search
 * 
 * @param request - Query parameters
 * @returns Query results with answer and sources
 * 
 * @example
 * ```typescript
 * const result = await queryKnowledgeBase({
 *   query: "What is Apple's revenue growth?",
 *   ticker: "AAPL",
 *   n_results: 5
 * });
 * console.log(result.answer);
 * ```
 */
export async function queryKnowledgeBase(
  request: QueryRequest
): Promise<QueryResponse> {
  return await fetchWithTimeout(`${API_BASE_URL}/api/query`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Run a new financial analysis for a company
 * 
 * This is a long-running operation (3-5 minutes).
 * Consider implementing polling or websockets for progress updates.
 * 
 * @param request - Analysis parameters
 * @returns Analysis status
 * 
 * @example
 * ```typescript
 * const status = await runAnalysis({
 *   ticker: "AAPL",
 *   force_refresh: false
 * });
 * 
 * if (status.status === 'completed') {
 *   console.log('Analysis complete!');
 * }
 * ```
 */
export async function runAnalysis(
  request: AnalysisRequest
): Promise<AnalysisStatus> {
  return await fetchWithTimeout(`${API_BASE_URL}/api/analyze`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Get full financial report for a company
 * 
 * @param ticker - Company ticker symbol (e.g., 'AAPL')
 * @returns Complete financial report
 */
export async function getFullReport(ticker: string): Promise<Report> {
  return await fetchWithTimeout(
    `${API_BASE_URL}/api/reports/${ticker.toUpperCase()}`
  );
}

/**
 * Compare multiple companies on a specific aspect
 * 
 * @param request - Comparison parameters
 * @returns Comparison results
 * 
 * @example
 * ```typescript
 * const comparison = await compareCompanies({
 *   tickers: ["AAPL", "MSFT", "GOOGL"],
 *   query: "profitability and profit margins",
 *   n_results_per_company: 3
 * });
 * ```
 */
export async function compareCompanies(
  request: CompareRequest
): Promise<any> {
  return await fetchWithTimeout(`${API_BASE_URL}/api/compare`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Check if the API is reachable
 */
export async function ping(): Promise<boolean> {
  try {
    await fetch(`${API_BASE_URL}/api/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000),
    });
    return true;
  } catch {
    return false;
  }
}

/**
 * Get formatted API base URL for display
 */
export function getAPIUrl(): string {
  return API_BASE_URL;
}

/**
 * Format confidence level for display
 */
export function formatConfidence(confidence: string): {
  label: string;
  color: string;
} {
  const formats = {
    high: { label: 'High Confidence', color: 'green' },
    medium: { label: 'Medium Confidence', color: 'yellow' },
    low: { label: 'Low Confidence', color: 'red' },
  };

  return formats[confidence as keyof typeof formats] || {
    label: 'Unknown',
    color: 'gray',
  };
}

/**
 * Format ticker for display
 */
export function formatTicker(ticker: string): string {
  return ticker.toUpperCase().trim();
}

/**
 * Validate ticker format
 */
export function isValidTicker(ticker: string): boolean {
  // Basic validation: 1-5 uppercase letters
  return /^[A-Z]{1,5}$/.test(ticker.toUpperCase());
}

// ============================================================================
// Development/Debug Helpers
// ============================================================================

if (import.meta.env.DEV) {
  console.log('🔧 API Integration loaded');
  console.log(`📡 API URL: ${API_BASE_URL}`);
  console.log(`⏱️  Timeout: ${TIMEOUT}ms`);
  
  // Expose to window for debugging
  (window as any).api = {
    checkHealth,
    getCompanies,
    queryKnowledgeBase,
    runAnalysis,
    getFullReport,
    compareCompanies,
    ping,
  };
}

export default {
  checkHealth,
  getCompanies,
  queryKnowledgeBase,
  runAnalysis,
  getFullReport,
  compareCompanies,
  ping,
  getAPIUrl,
  formatConfidence,
  formatTicker,
  isValidTicker,
};
