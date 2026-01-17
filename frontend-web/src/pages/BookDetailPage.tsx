/**
 * Book Detail Page
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Book, Heart } from 'lucide-react';
import { Header } from '@/components/Header';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Textarea';
import { bookAPI, libraryAPI, reviewAPI } from '@/services/api';
import { useToast } from '@/hooks/useToast';
import type { BookDetail } from '@/types';

export const BookDetailPage: React.FC = () => {
  const { bookId } = useParams<{ bookId: string }>();
  const [book, setBook] = useState<BookDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [rating, setRating] = useState(0);
  const [reviewText, setReviewText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  
  const navigate = useNavigate();
  const toast = useToast();

  useEffect(() => {
    if (bookId) {
      loadBook();
    }
  }, [bookId]);

  const loadBook = async () => {
    try {
      const data = await bookAPI.getDetails(bookId!);
      setBook(data);
      setRating(data.rating || 0);
      setReviewText(data.review || '');
    } catch (error) {
      toast.error('Failed to load book');
    } finally {
      setLoading(false);
    }
  };

  const handleAddToLibrary = async () => {
    try {
      await libraryAPI.addBook(bookId!);
      toast.success('Added to library!');
      loadBook();
    } catch (error) {
      toast.error('Failed to add to library');
    }
  };

  const handleSubmitReview = async () => {
    if (rating === 0) {
      toast.error('Please select a rating');
      return;
    }

    setSubmitting(true);
    try {
      await reviewAPI.createOrUpdate({
        book_id: bookId!,
        rating,
        review_text: reviewText.trim() || undefined,
      });
      toast.success('Review saved!');
      loadBook();
    } catch (error) {
      toast.error('Failed to save review');
    } finally {
      setSubmitting(false);
    }
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

  if (!book) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="text-center py-20">
          <p className="text-gray-600">Book not found</p>
          <Button 
            onClick={() => {
              const lastQuery = localStorage.getItem('lastSearchQuery');
              if (lastQuery) {
                navigate(`/search?q=${encodeURIComponent(lastQuery)}`);
              } else {
                navigate('/welcome');
              }
            }} 
            className="mt-4"
          >
            Back to Search
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-md p-8">
          <div className="md:flex gap-8">
            {/* Cover */}
            <div className="flex-shrink-0 mb-6 md:mb-0">
              {book.cover_url ? (
                <img
                  src={book.cover_url}
                  alt={book.title}
                  className="w-64 h-96 object-cover rounded-lg shadow-lg"
                />
              ) : (
                <div className="w-64 h-96 bg-gray-200 rounded-lg flex items-center justify-center">
                  <Book className="w-24 h-24 text-gray-400" />
                </div>
              )}
            </div>

            {/* Details */}
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{book.title}</h1>
              <p className="text-xl text-gray-600 mb-4">{book.author}</p>
              
              {/* Genres */}
              {book.genres.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4">
                  {book.genres.map((genre, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm"
                    >
                      {genre}
                    </span>
                  ))}
                </div>
              )}

              {/* Publication Info */}
              {book.publish_year && (
                <p className="text-gray-600 mb-4">
                  Published: {book.publish_year}
                  {book.publish_month && `/${book.publish_month}`}
                </p>
              )}

              {/* Description */}
              <p className="text-gray-700 mb-6">{book.description}</p>

              {/* Add to Library Button */}
              {!book.in_library && (
                <Button
                  variant="primary"
                  onClick={handleAddToLibrary}
                  className="mb-6"
                >
                  <Heart className="w-5 h-5 mr-2" />
                  Add to Library
                </Button>
              )}

              {/* Rating */}
              {book.in_library && (
                <div className="border-t pt-6">
                  <h3 className="text-lg font-semibold mb-3">Your Rating</h3>
                  <div className="flex gap-2 mb-4">
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((value) => (
                      <button
                        key={value}
                        onClick={() => setRating(value)}
                        className={`w-10 h-10 rounded-lg font-semibold transition-colors ${
                          value <= rating
                            ? 'bg-primary-600 text-white'
                            : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                        }`}
                      >
                        {value}
                      </button>
                    ))}
                  </div>

                  <Textarea
                    label="Review (optional)"
                    value={reviewText}
                    onChange={(e) => setReviewText(e.target.value)}
                    placeholder="Share your thoughts about this book..."
                    rows={4}
                  />

                  <Button
                    variant="primary"
                    onClick={handleSubmitReview}
                    isLoading={submitting}
                    className="mt-4"
                  >
                    Save Review
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
