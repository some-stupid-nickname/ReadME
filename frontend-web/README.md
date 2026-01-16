# Book Recommendation System - Frontend

React + TypeScript + Vite frontend for the Book Recommendation System.

## Features

- User authentication (register/login)
- Onboarding flow with book selection
- Personalized book search
- User library management
- Book reviews and ratings
- Admin metrics dashboard

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **React Router** - Routing
- **Axios** - HTTP client

## Setup

### Prerequisites

- Node.js 18+ and npm/yarn
- Running backend API (see backend/README.md)

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Update .env with your backend URL
# VITE_API_URL=http://localhost:8000
```

### Development

```bash
# Start development server
npm run dev

# Access at http://localhost:3000
```

### Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend-web/
├── src/
│   ├── components/     # Reusable components
│   │   ├── ui/        # Base UI components
│   │   ├── BookCard.tsx
│   │   ├── Header.tsx
│   │   └── ProtectedRoute.tsx
│   ├── contexts/      # React contexts
│   │   └── AuthContext.tsx
│   ├── hooks/         # Custom hooks
│   │   └── useToast.ts
│   ├── pages/         # Page components
│   │   ├── LoginPage.tsx
│   │   ├── OnboardingPage.tsx
│   │   ├── WelcomePage.tsx
│   │   ├── SearchResultsPage.tsx
│   │   ├── LibraryPage.tsx
│   │   ├── BookDetailPage.tsx
│   │   └── AdminMetricsPage.tsx
│   ├── services/      # API services
│   │   └── api.ts
│   ├── types/         # TypeScript types
│   │   └── index.ts
│   ├── App.tsx        # Root component
│   ├── main.tsx       # Entry point
│   └── index.css      # Global styles
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## Usage

### Authentication Flow

1. Register new account or login
2. Complete onboarding by selecting 3-10 favorite books
3. Access main search interface

### Search

- Search for books using natural language queries
- Personalized results based on your reading history
- Add books to your library
- View detailed book information

### Library

- View all saved books
- Sort by: recently added, rating, alphabetical
- Filter by rated books only
- Rate and review books (1-10 scale)

### Admin Metrics

- View system analytics
- User activity statistics
- Acceptance rates
- Average ratings

## Environment Variables

```bash
VITE_API_URL=http://localhost:8000  # Backend API URL
```

## License

Educational Project
