/**
 * Example React Component: Query Knowledge Base
 * 
 * This component demonstrates how to integrate the API into your React app.
 * Copy this pattern to update your existing Figma-generated components.
 * 
 * Location: Gradioappfrontend/src/components/QueryKnowledgeBase.tsx
 */

import React, { useState, useEffect } from 'react';
import { 
  queryKnowledgeBase, 
  getCompanies,
  type QueryResponse,
  type Company,
  APIError 
} from '../api/integration';

// Assuming you have these UI components from Radix/shadcn
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Loader2, Search, AlertCircle } from 'lucide-react';

export function QueryKnowledgeBase() {
  // State management
  const [query, setQuery] = useState('');
  const [ticker, setTicker] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);

  // Load available companies on mount
  useEffect(() => {
    loadCompanies();
  }, []);

  const loadCompanies = async () => {
    try {
      const data = await getCompanies();
      setCompanies(data);
    } catch (err) {
      console.error('Failed to load companies:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await queryKnowledgeBase({
        query: query.trim(),
        ticker: ticker.trim() || undefined,
        n_results: 5
      });
      
      setResult(response);
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
        
        // Handle specific error cases
        if (err.statusCode === 503) {
          setError('Knowledge base is not available. Please try again later.');
        } else if (err.statusCode === 408) {
          setError('Request timed out. The system may be processing your query.');
        }
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
      console.error('Query error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
  };

  const getConfidenceBadgeColor = (confidence: string) => {
    switch (confidence) {
      case 'high':
        return 'bg-green-100 text-green-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Query Knowledge Base</h1>
        <p className="text-gray-600">
          Ask questions about companies in our financial analysis database.
        </p>
      </div>

      {/* Available Companies */}
      {companies.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Available Companies ({companies.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {companies.slice(0, 10).map((company) => (
                <Badge
                  key={company.ticker}
                  variant="outline"
                  className="cursor-pointer hover:bg-gray-100"
                  onClick={() => setTicker(company.ticker)}
                >
                  {company.ticker}
                </Badge>
              ))}
              {companies.length > 10 && (
                <Badge variant="outline">
                  +{companies.length - 10} more
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Query Form */}
      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Query Input */}
            <div className="space-y-2">
              <label htmlFor="query" className="text-sm font-medium">
                Your Question
              </label>
              <div className="relative">
                <Input
                  id="query"
                  type="text"
                  placeholder="e.g., What is Apple's revenue growth trend?"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="pr-10"
                  disabled={loading}
                />
                <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              </div>
            </div>

            {/* Ticker Filter */}
            <div className="space-y-2">
              <label htmlFor="ticker" className="text-sm font-medium">
                Filter by Ticker (Optional)
              </label>
              <Input
                id="ticker"
                type="text"
                placeholder="e.g., AAPL, MSFT, GOOGL"
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                maxLength={5}
                disabled={loading}
              />
              <p className="text-xs text-gray-500">
                Leave blank to search across all companies
              </p>
            </div>

            {/* Submit Button */}
            <Button 
              type="submit" 
              disabled={loading || !query.trim()}
              className="w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Search Knowledge Base
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {loading && (
        <Card>
          <CardContent className="py-12">
            <div className="flex flex-col items-center justify-center space-y-4">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              <p className="text-gray-600">
                Searching through financial analyses...
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results Display */}
      {result && !loading && (
        <div className="space-y-6">
          {/* Answer Card */}
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between">
                <CardTitle>Answer</CardTitle>
                <Badge className={getConfidenceBadgeColor(result.confidence)}>
                  {result.confidence.toUpperCase()} CONFIDENCE
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="prose max-w-none">
                <p className="whitespace-pre-wrap leading-relaxed">
                  {result.answer}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Sources */}
          {result.sources.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Sources ({result.sources.length})</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {result.sources.map((source, idx) => (
                  <div
                    key={idx}
                    className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="font-mono">
                          {source.ticker}
                        </Badge>
                        <span className="text-sm text-gray-600">
                          {source.type.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500">
                        Relevance: {((1 - source.distance) * 100).toFixed(0)}%
                      </div>
                    </div>
                    <p className="text-sm text-gray-700 leading-relaxed">
                      {source.content}
                    </p>
                    {source.timestamp && (
                      <p className="text-xs text-gray-500 mt-2">
                        {new Date(source.timestamp).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Follow-up Suggestions */}
          {result.suggestions.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Suggested Follow-up Questions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {result.suggestions.map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:border-blue-400 hover:bg-blue-50 transition-colors text-sm"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Empty State */}
      {!loading && !result && !error && (
        <Card>
          <CardContent className="py-12">
            <div className="text-center space-y-4">
              <Search className="h-12 w-12 text-gray-400 mx-auto" />
              <div className="space-y-2">
                <h3 className="text-lg font-medium text-gray-900">
                  Ready to search
                </h3>
                <p className="text-gray-600">
                  Enter a question above to query the financial knowledge base
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default QueryKnowledgeBase;
