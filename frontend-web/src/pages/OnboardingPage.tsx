/**
 * Onboarding Page - Select favorite books
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, Book } from 'lucide-react';
import { onboardingAPI } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/hooks/useToast';
import type { OnboardingBook } from '@/types';

export const OnboardingPage: React.FC = () => {
  const [books, setBooks] = useState<OnboardingBook[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const { refreshProfile } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();

  useEffect(() => {
    loadBooks();
  }, []);

  const loadBooks = async () => {
    try {
      const data = await onboardingAPI.getBooks();
      setBooks(data);
    } catch (error) {
      toast.error('Failed to load books');
    } finally {
      setLoading(false);
    }
  };

  const toggleBook = (bookId: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(bookId)) {
      newSelected.delete(bookId);
    } else {
      newSelected.add(bookId);
    }
    setSelectedIds(newSelected);
  };

  const handleComplete = async () => {
    if (selectedIds.size < 3) {
      toast.error('Please select at least 3 books');
      return;
    }
    if (selectedIds.size > 10) {
      toast.error('Please select at most 10 books');
      return;
    }

    setSubmitting(true);
    try {
      await onboardingAPI.complete({ selected_book_ids: Array.from(selectedIds) });
      await refreshProfile();
      toast.success('Onboarding complete!');
      navigate('/welcome');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to complete onboarding');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const categories = ['classic', 'fantasy', 'thriller', 'modern'];

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Choose Your Favorites
          </h1>
          <p className="text-lg text-gray-600">
            Select 3-10 books you love to personalize your recommendations
          </p>
          <div className="mt-4 inline-flex items-center px-4 py-2 bg-primary-100 text-primary-700 rounded-full">
            <span className="font-medium">
              {selectedIds.size} / 10 selected
              {selectedIds.size >= 3 && ' ✓'}
            </span>
          </div>
        </div>

        {/* Books Grid */}
        {categories.map((category) => {
          const categoryBooks = books.filter((b) => b.category === category);
          if (categoryBooks.length === 0) return null;

          return (
            <div key={category} className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4 capitalize">
                {category}
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {categoryBooks.map((book) => {
                  const isSelected = selectedIds.has(book.book_id);

                  return (
                    <button
                      key={book.book_id}
                      onClick={() => toggleBook(book.book_id)}
                      className={`relative bg-white rounded-lg shadow-md hover:shadow-lg transition-all p-4 text-left ${
                        isSelected ? 'ring-2 ring-primary-600' : ''
                      }`}
                    >
                      {/* Cover */}
                      <div className="mb-3">
                        {book.cover_url ? (
                          <img
                            src={book.cover_url}
                            alt={book.title}
                            className="w-full h-40 object-cover rounded"
                          />
                        ) : (
                          <div className="w-full h-40 bg-gray-200 rounded flex items-center justify-center">
                            <Book className="w-12 h-12 text-gray-400" />
                          </div>
                        )}
                      </div>

                      {/* Title & Author */}
                      <h3 className="font-semibold text-sm text-gray-900 line-clamp-2 mb-1">
                        {book.title}
                      </h3>
                      <p className="text-xs text-gray-600">{book.author}</p>

                      {/* Check Mark */}
                      {isSelected && (
                        <div className="absolute top-2 right-2 bg-primary-600 text-white rounded-full p-1">
                          <Check className="w-4 h-4" />
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}

        {/* Complete Button */}
        <div className="flex justify-center mt-8">
          <Button
            variant="primary"
            size="lg"
            onClick={handleComplete}
            isLoading={submitting}
            disabled={selectedIds.size < 3}
            className="px-12"
          >
            Complete Onboarding
          </Button>
        </div>
      </div>
    </div>
  );
};
