/**
 * Search Results Page
 */
import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, useNavigationType } from 'react-router-dom';
import { Header } from '@/components/Header';
import { BookCard } from '@/components/BookCard';
import { searchAPI, libraryAPI } from '@/services/api';
import { useToast } from '@/hooks/useToast';
import { useAuth } from '@/contexts/AuthContext';
import type { PersonalizedSearchResponse } from '@/types';

export const SearchResultsPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  
  const [results, setResults] = useState<PersonalizedSearchResponse | null>(null);
  const [loading, setLoading] = useState(true);
  
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
            setLoading(false);
            // Save query to localStorage for back navigation (detail page fallback)
            localStorage.setItem('lastSearchQuery', query);
            return;
          } catch {
            // ignore cache parse errors and fall back to live search
          }
        }
      }

      performSearch();
      // Save query to localStorage for back navigation
      localStorage.setItem('lastSearchQuery', query);
    }
  }, [query, navigationType]);

  const performSearch = async () => {
    setLoading(true);
    try {
      // Use personalized search if authenticated
      const data = await searchAPI.personalizedSearch(query);
      setResults(data);
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

  const handleAddToLibrary = async (bookId: string) => {
    try {
      await libraryAPI.addBook(bookId, query);
      toast.success('Added to library!');
      await refreshProfile();
      // Refresh results to update "in_library" status
      performSearch();
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
                book={{ ...book, book_id: book.id, in_library: false }}
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
