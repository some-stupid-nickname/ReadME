/**
 * Header Navigation Component
 */
import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Book, Library, Search, LogOut, BarChart3 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from './ui/Button';

export const Header: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/welcome" className="flex items-center space-x-2">
            <Book className="w-8 h-8 text-primary-600" />
            <span className="text-xl font-bold text-gray-900">BookRec</span>
          </Link>

          {/* Navigation */}
          {user && (
            <nav className="flex items-center space-x-4">
              <Link
                to="/welcome"
                className={`flex items-center px-3 py-2 rounded-lg transition-colors ${
                  isActive('/welcome')
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <Search className="w-5 h-5 mr-2" />
                <span className="hidden sm:inline">Search</span>
              </Link>

              <Link
                to="/library"
                className={`flex items-center px-3 py-2 rounded-lg transition-colors ${
                  isActive('/library')
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <Library className="w-5 h-5 mr-2" />
                <span className="hidden sm:inline">Library</span>
                {user.library_count > 0 && (
                  <span className="ml-2 px-2 py-0.5 text-xs bg-primary-600 text-white rounded-full">
                    {user.library_count}
                  </span>
                )}
              </Link>

              <Link
                to="/admin"
                className={`flex items-center px-3 py-2 rounded-lg transition-colors ${
                  isActive('/admin')
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <BarChart3 className="w-5 h-5 mr-2" />
                <span className="hidden sm:inline">Metrics</span>
              </Link>

              <div className="border-l pl-4 ml-4 flex items-center space-x-3">
                <span className="text-sm text-gray-600 hidden sm:inline">
                  {user.username}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleLogout}
                  className="flex items-center"
                >
                  <LogOut className="w-4 h-4 mr-1" />
                  <span className="hidden sm:inline">Logout</span>
                </Button>
              </div>
            </nav>
          )}
        </div>
      </div>
    </header>
  );
};
