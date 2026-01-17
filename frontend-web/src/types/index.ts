/**
 * TypeScript type definitions for the Book Recommendation System
 */

// ============================================================
// Book Types
// ============================================================

export interface BookInfo {
  id: string;
  title: string;
  author: string;
  genres: string[];
  description: string;
  cover_url?: string | null;
  source_link?: string | null;
}

export interface BookDetail extends BookInfo {
  book_id: string;
  authors: string;
  category: string;
  publish_year?: number | null;
  publish_month?: number | null;
  cover_url?: string | null;
  in_library: boolean;
  added_at?: string | null;
  rating?: number | null;
  review?: string | null;
}

// ============================================================
// Search Types
// ============================================================

export interface SearchRequest {
  query: string;
}

export interface SearchResponse {
  response: string;
  books: BookInfo[];
  message_id?: number | null;
}

export interface PersonalizedSearchResponse extends SearchResponse {
  personalization_applied: boolean;
  similarity_score?: number | null;
  context_books?: string[] | null;
}

export interface ClarificationRequest {
  query: string;
}

export interface ClarificationResponse {
  is_vague: boolean;
  clarifying_questions?: string | null;
  original_query: string;
}

export interface EnrichedSearchRequest {
  original_query: string;
  user_context: string;
}

// ============================================================
// Auth Types
// ============================================================

export interface UserRegister {
  username: string;
  password: string;
}

export interface UserLogin {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: number;
}

export interface UserProfile {
  user_id: number;
  username: string;
  onboarding_completed: boolean;
  library_count: number;
}

// ============================================================
// Onboarding Types
// ============================================================

export interface OnboardingBook {
  book_id: string;
  title: string;
  author: string;
  category: string;
  cover_url?: string | null;
}

export interface OnboardingComplete {
  selected_book_ids: string[];
}

// ============================================================
// Library Types
// ============================================================

export interface LibraryResponse {
  books: BookDetail[];
}

// ============================================================
// Review Types
// ============================================================

export interface ReviewRequest {
  book_id: string;
  rating: number;
  review_text?: string;
}

export interface ReviewResponse {
  book_id: string;
  rating: number;
  review_text?: string | null;
  created_at: string;
  updated_at: string;
}

// ============================================================
// Metrics Types
// ============================================================

export interface MetricsResponse {
  total_users: number;
  active_users_7d: number;
  total_queries_all_time: number;
  total_queries_today: number;
  total_queries_week: number;
  primary_acceptance_rate: number;
  final_acceptance_rate: number;
  avg_library_size: number;
  avg_rating: number;
  median_rating: number;
}

// ============================================================
// Error Types
// ============================================================

export interface APIError {
  detail: string;
}
