/**
 * Search Results Page
 */
import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
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
  
  const { user, refreshProfile } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();

  useEffect(() => {
    if (query) {
      performSearch();
    }
  }, [query]);

  const performSearch = async () => {
    setLoading(true);
    try {
      // Use personalized search if authenticated
      const data = await searchAPI.personalizedSearch(query);
      setResults(data);
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
                book={{ ...book, book_id: book.id, cover_url: null, in_library: false }}
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
