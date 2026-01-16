/**
 * API Client for Book Recommendation Backend
 */
import axios, { AxiosError } from 'axios';
import type {
  UserRegister,
  UserLogin,
  TokenResponse,
  UserProfile,
  OnboardingBook,
  OnboardingComplete,
  SearchRequest,
  SearchResponse,
  PersonalizedSearchResponse,
  LibraryResponse,
  ReviewRequest,
  ReviewResponse,
  BookDetail,
  MetricsResponse,
} from '@/types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Handle errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// ============================================================
// Authentication API
// ============================================================

export const authAPI = {
  register: async (data: UserRegister): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/api/auth/register', data);
    return response.data;
  },

  login: async (data: UserLogin): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/api/auth/login', data);
    return response.data;
  },

  getProfile: async (): Promise<UserProfile> => {
    const response = await api.get<UserProfile>('/api/auth/me');
    return response.data;
  },
};

// ============================================================
// Onboarding API
// ============================================================

export const onboardingAPI = {
  getBooks: async (): Promise<OnboardingBook[]> => {
    const response = await api.get<OnboardingBook[]>('/api/onboarding/books');
    return response.data;
  },

  complete: async (data: OnboardingComplete): Promise<{ success: boolean; library_count: number }> => {
    const response = await api.post('/api/onboarding/complete', data);
    return response.data;
  },
};

// ============================================================
// Search API
// ============================================================

export const searchAPI = {
  search: async (query: string): Promise<SearchResponse> => {
    const response = await api.post<SearchResponse>('/api/search', { query });
    return response.data;
  },

  personalizedSearch: async (query: string): Promise<PersonalizedSearchResponse> => {
    const response = await api.post<PersonalizedSearchResponse>('/api/search/personalized', { query });
    return response.data;
  },
};

// ============================================================
// Library API
// ============================================================

export const libraryAPI = {
  getLibrary: async (sort?: string, ratedOnly?: boolean): Promise<LibraryResponse> => {
    const response = await api.get<LibraryResponse>('/api/library', {
      params: { sort, rated_only: ratedOnly },
    });
    return response.data;
  },

  addBook: async (bookId: string, sourceQuery?: string): Promise<void> => {
    await api.post(`/api/library/${bookId}`, { source_query: sourceQuery });
  },

  removeBook: async (bookId: string): Promise<void> => {
    await api.delete(`/api/library/${bookId}`);
  },
};

// ============================================================
// Review API
// ============================================================

export const reviewAPI = {
  createOrUpdate: async (data: ReviewRequest): Promise<ReviewResponse> => {
    const response = await api.post<ReviewResponse>('/api/reviews', data);
    return response.data;
  },

  getReview: async (bookId: string): Promise<ReviewResponse> => {
    const response = await api.get<ReviewResponse>(`/api/reviews/${bookId}`);
    return response.data;
  },

  deleteReview: async (bookId: string): Promise<void> => {
    await api.delete(`/api/reviews/${bookId}`);
  },
};

// ============================================================
// Book API
// ============================================================

export const bookAPI = {
  getDetails: async (bookId: string): Promise<BookDetail> => {
    const response = await api.get<BookDetail>(`/api/books/${bookId}`);
    return response.data;
  },
};

// ============================================================
// Admin API
// ============================================================

export const adminAPI = {
  getMetrics: async (): Promise<MetricsResponse> => {
    const response = await api.get<MetricsResponse>('/api/admin/metrics');
    return response.data;
  },
};

export default api;
