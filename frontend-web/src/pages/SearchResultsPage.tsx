/**
 * Search Results Page with Query Enrichment
 */
import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, useNavigationType } from 'react-router-dom';
import { Header } from '@/components/Header';
import { BookCard } from '@/components/BookCard';
import { searchAPI, libraryAPI } from '@/services/api';
import { useToast } from '@/hooks/useToast';
import { useAuth } from '@/contexts/AuthContext';
import type { PersonalizedSearchResponse, ClarificationResponse } from '@/types';
import { Textarea } from '@/components/ui/Textarea';
import { Button } from '@/components/ui/Button';

export const SearchResultsPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  
  const [results, setResults] = useState<PersonalizedSearchResponse | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Query enrichment state
  const [clarification, setClarification] = useState<ClarificationResponse | null>(null);
  const [userContext, setUserContext] = useState('');
  const [isEnriching, setIsEnriching] = useState(false);
  
  const { refreshProfile } = useAuth();
  const navigate = useNavigate();
  const navigationType = useNavigationType();
  const toast = useToast();

  useEffect(() => {
    if (query) {
      const cacheKey = `searchResults:${query}`;

      // If user returned via browser back (POP), reuse cached results and avoid re-searching.
      if (navigationType === 'POP') {
        const cached = sessionStorage.getItem(cacheKey);
        if (cached) {
          try {
            const parsed = JSON.parse(cached) as PersonalizedSearchResponse;
            setResults(parsed);
            setClarification(null);
            setLoading(false);
            // Save query to localStorage for back navigation (detail page fallback)
            localStorage.setItem('lastSearchQuery', query);
            return;
          } catch {
            // ignore cache parse errors and fall back to live search
          }
        }
      }

      // Reset state for new search
      setClarification(null);
      setUserContext('');
      setResults(null);
      
      // First check if query needs clarification
      checkClarification();
      // Save query to localStorage for back navigation
      localStorage.setItem('lastSearchQuery', query);
    }
  }, [query, navigationType]);

  const checkClarification = async () => {
    setLoading(true);
    try {
      const clarifyResponse = await searchAPI.clarifyQuery(query);
      
      if (clarifyResponse.is_vague && clarifyResponse.clarifying_questions) {
        // Query is vague - show clarifying questions
        setClarification(clarifyResponse);
        setLoading(false);
      } else {
        // Query is clear - proceed with search
        await performSearch();
      }
    } catch (error: any) {
      // If clarification fails, fall back to direct search
      console.warn('Clarification check failed, proceeding with direct search:', error);
      await performSearch();
    }
  };

  const performSearch = async () => {
    setLoading(true);
    try {
      // Use personalized search if authenticated
      const data = await searchAPI.personalizedSearch(query);
      setResults(data);
      setClarification(null);
      try {
        sessionStorage.setItem(`searchResults:${query}`, JSON.stringify(data));
      } catch {
        // ignore storage errors (e.g., quota)
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleEnrichedSearch = async () => {
    if (!userContext.trim()) {
      toast.error('Please provide some details');
      return;
    }
    
    setIsEnriching(true);
    try {
      const data = await searchAPI.enrichedSearch(query, userContext.trim());
      setResults(data as PersonalizedSearchResponse);
      setClarification(null);
      try {
        sessionStorage.setItem(`searchResults:${query}`, JSON.stringify(data));
      } catch {
        // ignore storage errors
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Search failed');
    } finally {
      setIsEnriching(false);
    }
  };

  const handleSkipClarification = async () => {
    setClarification(null);
    await performSearch();
  };

  const handleAddToLibrary = async (bookId: string) => {
    try {
      await libraryAPI.addBook(bookId, query);
      toast.success('Added to library!');
      await refreshProfile();
      // Update local state to mark book as in library (no need to re-search)
      if (results) {
        setResults({
          ...results,
          books: results.books.map(book => 
            book.id === bookId ? { ...book, in_library: true } : book
          )
        });
      }
    } catch (error) {
      toast.error('Failed to add to library');
    }
  };

  const handleViewDetails = (bookId: string) => {
    navigate(`/book/${bookId}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  // Show clarifying questions if query is vague
  if (clarification && clarification.is_vague) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="max-w-2xl mx-auto px-4 py-8">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h1 className="text-xl font-bold text-gray-900 mb-2">
              🔍 Searching for: "{query}"
            </h1>
            
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
              <p className="text-amber-800 whitespace-pre-line">
                {clarification.clarifying_questions}
              </p>
            </div>
            
            <div className="space-y-4">
              <Textarea
                placeholder="Tell me more about what you're looking for..."
                value={userContext}
                onChange={(e) => setUserContext(e.target.value)}
                rows={3}
                className="w-full"
              />
              
              <div className="flex gap-3">
                <Button
                  onClick={handleEnrichedSearch}
                  disabled={isEnriching || !userContext.trim()}
                  className="flex-1"
                >
                  {isEnriching ? 'Searching...' : 'Search with details'}
                </Button>
                
                <Button
                  variant="outline"
                  onClick={handleSkipClarification}
                  disabled={isEnriching}
                >
                  Search anyway
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Search Info */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Search Results for "{query}"
          </h1>
          
          {results?.personalization_applied && (
            <div className="bg-primary-50 border border-primary-200 rounded-lg p-3 mb-4">
              <p className="text-sm text-primary-800">
                ✨ Personalized based on your reading preferences
                {results.context_books && results.context_books.length > 0 && (
                  <span className="ml-2">
                    (Similar to: {results.context_books.slice(0, 2).join(', ')})
                  </span>
                )}
              </p>
            </div>
          )}
        </div>

        {/* AI Response */}
        {results?.response && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <p className="text-gray-800 whitespace-pre-line">{results.response}</p>
          </div>
        )}

        {/* Books Grid */}
        {results?.books && results.books.length > 0 ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {results.books.map((book) => (
              <BookCard
                key={book.id}
                book={{ ...book, book_id: book.id, in_library: (book as any).in_library || false }}
                onAddToLibrary={handleAddToLibrary}
                onViewDetails={handleViewDetails}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-600">No books found. Try a different search!</p>
          </div>
        )}
      </div>
    </div>
  );
};
