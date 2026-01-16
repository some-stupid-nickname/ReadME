/**
 * Book Card Component
 */
import React from 'react';
import { Book, Heart } from 'lucide-react';
import type { BookDetail } from '@/types';
import { Button } from './ui/Button';

interface BookCardProps {
  book: BookDetail | {
    book_id: string;
    title: string;
    author: string;
    genres?: string[];
    description: string;
    cover_url?: string | null;
    in_library?: boolean;
  };
  onAddToLibrary?: (bookId: string) => void;
  onViewDetails?: (bookId: string) => void;
  compact?: boolean;
}

export const BookCard: React.FC<BookCardProps> = ({
  book,
  onAddToLibrary,
  onViewDetails,
  compact = false,
}) => {
  const bookId = 'book_id' in book ? book.book_id : '';
  const coverUrl = book.cover_url;
  const genres = book.genres || [];
  const inLibrary = 'in_library' in book ? book.in_library : false;

  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-4 flex flex-col">
      {/* Cover Image */}
      <div className="flex-shrink-0 mb-3">
        {coverUrl ? (
          <img
            src={coverUrl}
            alt={book.title}
            className="w-full h-48 object-cover rounded-lg"
            onError={(e) => {
              e.currentTarget.style.display = 'none';
              e.currentTarget.nextElementSibling?.classList.remove('hidden');
            }}
          />
        ) : null}
        <div className={clsx('w-full h-48 bg-gray-200 rounded-lg flex items-center justify-center', coverUrl && 'hidden')}>
          <Book className="w-16 h-16 text-gray-400" />
        </div>
      </div>

      {/* Book Info */}
      <div className="flex-1">
        <h3 className="font-semibold text-lg text-gray-900 mb-1 line-clamp-2">
          {book.title}
        </h3>
        <p className="text-sm text-gray-600 mb-2">{book.author}</p>

        {genres.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-2">
            {genres.slice(0, 3).map((genre, idx) => (
              <span
                key={idx}
                className="text-xs px-2 py-1 bg-primary-100 text-primary-700 rounded-full"
              >
                {genre}
              </span>
            ))}
          </div>
        )}

        {!compact && (
          <p className="text-sm text-gray-600 line-clamp-3 mb-3">
            {book.description}
          </p>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2 mt-auto pt-3 border-t">
        {onViewDetails && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => onViewDetails(bookId)}
            className="flex-1"
          >
            Details
          </Button>
        )}
        {onAddToLibrary && !inLibrary && (
          <Button
            variant="primary"
            size="sm"
            onClick={() => onAddToLibrary(bookId)}
            className="flex-1"
          >
            <Heart className="w-4 h-4 mr-1" />
            Add
          </Button>
        )}
        {inLibrary && (
          <span className="flex-1 flex items-center justify-center text-sm text-green-600">
            <Heart className="w-4 h-4 mr-1 fill-current" />
            In Library
          </span>
        )}
      </div>
    </div>
  );
};

function clsx(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(' ');
}
