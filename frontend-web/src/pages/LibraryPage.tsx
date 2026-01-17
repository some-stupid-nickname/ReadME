/**
 * User Library Page
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Header } from '@/components/Header';
import { BookCard } from '@/components/BookCard';
import { Button } from '@/components/ui/Button';
import { libraryAPI } from '@/services/api';
import { useToast } from '@/hooks/useToast';
import type { BookDetail } from '@/types';

export const LibraryPage: React.FC = () => {
  const [books, setBooks] = useState<BookDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [sort, setSort] = useState<string>('added_at');
  
  const navigate = useNavigate();
  const toast = useToast();

  useEffect(() => {
    loadLibrary();
  }, [sort]);

  const loadLibrary = async () => {
    setLoading(true);
    try {
      const data = await libraryAPI.getLibrary(sort);
      setBooks(data.books);
    } catch (error) {
      toast.error('Failed to load library');
    } finally {
      setLoading(false);
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
        {/* Header */}
        <div className="mb-6 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">
            My Library ({books.length})
          </h1>
          
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg"
          >
            <option value="added_at">Recently Added</option>
            <option value="rating">Highest Rated</option>
            <option value="alphabetical">Alphabetical</option>
          </select>
        </div>

        {/* Books Grid */}
        {books.length > 0 ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {books.map((book) => (
              <BookCard
                key={book.book_id}
                book={book}
                onViewDetails={handleViewDetails}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-20">
            <p className="text-gray-600 mb-4">Your library is empty</p>
            <Button variant="primary" onClick={() => navigate('/welcome')}>
              Start Searching
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};
