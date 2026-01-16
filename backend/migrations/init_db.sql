-- Initialize PostgreSQL database schema
-- This file is executed automatically by docker-compose on first run

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    onboarding_completed BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- User library table
CREATE TABLE IF NOT EXISTS user_library (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    book_id VARCHAR(50) NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(20),
    source_query TEXT,
    UNIQUE(user_id, book_id)
);

CREATE INDEX IF NOT EXISTS idx_library_user ON user_library(user_id);
CREATE INDEX IF NOT EXISTS idx_library_book ON user_library(book_id);
CREATE INDEX IF NOT EXISTS idx_library_added_at ON user_library(added_at DESC);

-- User reviews table
CREATE TABLE IF NOT EXISTS user_reviews (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    book_id VARCHAR(50) NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 10),
    review_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, book_id)
);

CREATE INDEX IF NOT EXISTS idx_reviews_user ON user_reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_reviews_book ON user_reviews(book_id);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON user_reviews(rating);
CREATE INDEX IF NOT EXISTS idx_reviews_updated ON user_reviews(updated_at DESC);

-- User preference vectors table
CREATE TABLE IF NOT EXISTS user_preference_vectors (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    preference_vector BYTEA NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    books_count INTEGER DEFAULT 0,
    needs_recalculation BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_preference_needs_update 
    ON user_preference_vectors(needs_recalculation) 
    WHERE needs_recalculation = TRUE;

-- Recommendation logs table
CREATE TABLE IF NOT EXISTS recommendation_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    query TEXT NOT NULL,
    returned_book_ids TEXT[],
    liked_book_ids TEXT[],
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    personalization_used BOOLEAN DEFAULT FALSE,
    similarity_score FLOAT
);

CREATE INDEX IF NOT EXISTS idx_logs_user ON recommendation_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON recommendation_logs(timestamp DESC);

-- Book covers cache table
CREATE TABLE IF NOT EXISTS book_covers (
    book_id VARCHAR(50) PRIMARY KEY,
    cover_url TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(20) DEFAULT 'google_books',
    fetch_failed BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_covers_fetched ON book_covers(fetched_at DESC);

-- Onboarding books table
CREATE TABLE IF NOT EXISTS onboarding_books (
    id SERIAL PRIMARY KEY,
    book_id VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    display_order INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    UNIQUE(category, display_order)
);

CREATE INDEX IF NOT EXISTS idx_onboarding_category 
    ON onboarding_books(category, display_order);

-- Insert placeholder onboarding books
-- These will be updated with real book_ids from SQLite using populate_onboarding_books.py script
INSERT INTO onboarding_books (book_id, category, display_order, title, author) VALUES
-- Classic (4 books)
('classic_1', 'classic', 1, 'War and Peace', 'Leo Tolstoy'),
('classic_2', 'classic', 2, '1984', 'George Orwell'),
('classic_3', 'classic', 3, 'Pride and Prejudice', 'Jane Austen'),
('classic_4', 'classic', 4, 'The Master and Margarita', 'Mikhail Bulgakov'),

-- Fantasy (4 books)
('fantasy_1', 'fantasy', 1, 'Harry Potter and the Sorcerer''s Stone', 'J.K. Rowling'),
('fantasy_2', 'fantasy', 2, 'The Lord of the Rings', 'J.R.R. Tolkien'),
('fantasy_3', 'fantasy', 3, 'The Hitchhiker''s Guide to the Galaxy', 'Douglas Adams'),
('fantasy_4', 'fantasy', 4, 'Dune', 'Frank Herbert'),

-- Thriller (4 books)
('thriller_1', 'thriller', 1, 'The Girl with the Dragon Tattoo', 'Stieg Larsson'),
('thriller_2', 'thriller', 2, 'Murder on the Orient Express', 'Agatha Christie'),
('thriller_3', 'thriller', 3, 'The Silence of the Lambs', 'Thomas Harris'),
('thriller_4', 'thriller', 4, 'Sherlock Holmes', 'Arthur Conan Doyle'),

-- Modern (4 books)
('modern_1', 'modern', 1, 'A Little Life', 'Hanya Yanagihara'),
('modern_2', 'modern', 2, 'Three Comrades', 'Erich Maria Remarque'),
('modern_3', 'modern', 3, 'One Hundred Years of Solitude', 'Gabriel García Márquez'),
('modern_4', 'modern', 4, 'Norwegian Wood', 'Haruki Murakami')
ON CONFLICT DO NOTHING;
