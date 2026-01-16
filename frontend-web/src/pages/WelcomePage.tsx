/**
 * Welcome/Search Page - Main page after login
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search } from 'lucide-react';
import { Header } from '@/components/Header';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useAuth } from '@/contexts/AuthContext';

export const WelcomePage: React.FC = () => {
  const [query, setQuery] = useState('');
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="max-w-4xl mx-auto px-4 py-16">
        {/* Welcome Message */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome back, {user?.username}!
          </h1>
          <p className="text-xl text-gray-600">
            What would you like to read today?
          </p>
        </div>

        {/* Search Box */}
        <form onSubmit={handleSearch} className="mb-12">
          <div className="relative">
            <Input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search for books, authors, genres..."
              className="pl-12 text-lg py-4"
            />
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <Button
              type="submit"
              variant="primary"
              className="absolute right-2 top-1/2 transform -translate-y-1/2"
            >
              Search
            </Button>
          </div>
        </form>

        {/* Quick Links */}
        <div className="grid md:grid-cols-2 gap-6">
          <div 
            onClick={() => navigate('/library')}
            className="bg-white rounded-lg shadow-md p-6 cursor-pointer hover:shadow-lg transition-shadow"
          >
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              My Library
            </h3>
            <p className="text-gray-600">
              {user?.library_count || 0} books in your collection
            </p>
          </div>

          <div 
            onClick={() => setQuery('popular books 2024')}
            className="bg-white rounded-lg shadow-md p-6 cursor-pointer hover:shadow-lg transition-shadow"
          >
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Discover Popular Books
            </h3>
            <p className="text-gray-600">
              Find trending and highly-rated books
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
