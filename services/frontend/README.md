# BD Law Assistant - Frontend

## Overview

The frontend application for Bangladesh Law Assistant is a modern web application built with Next.js 15, React 19, and TypeScript. It provides a bilingual (English/Bengali) interface for legal document search, AI-powered Q&A, and user authentication through the Gateway API.

## Features

- **Bilingual Interface** - Full support for English and Bengali
- **Legal Search** - Advanced search for Bangladesh laws and regulations
- **AI Chat Assistant** - Q&A powered by RAG service with Gemini 2.5 Flash
- **User Authentication** - JWT-based auth via Gateway
- **Responsive Design** - Mobile-first design with Tailwind CSS
- **Dark Mode** - System-based theme switching
- **Internationalization** - next-intl for i18n support
- **State Management** - Zustand for global state
- **Form Validation** - React Hook Form + Zod schemas

## Tech Stack

| Category | Technology | Version |
|----------|------------|---------|
| Framework | Next.js | 15.5.3 |
| UI Library | React | 19.1.0 |
| Language | TypeScript | 5.x |
| Styling | Tailwind CSS | 4.x |
| HTTP Client | Axios | 1.12.2 |
| State Management | Zustand | 5.0.8 |
| Forms | React Hook Form | 7.63.0 |
| Validation | Zod | 4.1.9 |
| i18n | next-intl | 4.3.9 |
| Icons | Lucide React | 0.544.0 |

## Architecture

```
┌──────────────────────────────────────┐
│          Next.js Frontend            │
│         (Port 3000/3002)             │
│                                      │
│  ┌────────────────────────────────┐ │
│  │    Pages & Components          │ │
│  │  • / (Home)                    │ │
│  │  • /auth/login                 │ │
│  │  • /auth/register              │ │
│  │  • /dashboard/*                │ │
│  │                                │ │
│  │    State Management            │ │
│  │  • Zustand Stores              │ │
│  │  • Auth State                  │ │
│  └────────────────────────────────┘ │
│                                      │
│  ┌────────────────────────────────┐ │
│  │      API Layer (lib/api)       │ │
│  │  • gatewayClient (Axios)       │ │
│  │  • Token Management            │ │
│  │  • Auto Token Refresh          │ │
│  └────────────────────────────────┘ │
└──────────────────────────────────────┘
              ↓
    HTTP Requests with JWT
              ↓
┌──────────────────────────────────────┐
│       API Gateway (8081)             │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│      Backend Services                │
│  • RAG Service (8000)                │
│  • Scraper Service (8001)            │
└──────────────────────────────────────┘
```

### API Integration

The frontend communicates with backend services through the Gateway API:

1. **Gateway Client** (`lib/api/client.ts`) - Axios client with JWT token management
2. **Service Layers** (`lib/api/services/`) - Auth, user, chat, search services
3. **Token Management** - Automatic token refresh on 401 errors
4. **Cookie Storage** - Secure token storage with httpOnly cookies

## Prerequisites

- **Node.js 20+** - JavaScript runtime
- **npm** - Package manager
- **Gateway Service** - Running on port 8081
- **RAG Service** - Running on port 8000 (accessed via gateway)

## Installation

### 1. Install Dependencies

```bash
cd services/frontend
npm install
```

### 2. Configuration

Copy the environment template:

```bash
cp .env.example .env.local
```

Edit `.env.local`:

```bash
# API URLs
NEXT_PUBLIC_GATEWAY_URL=http://localhost:8081
NEXT_PUBLIC_RAG_URL=http://localhost:8000

# Application
NEXT_PUBLIC_APP_NAME=BD Law Assistant
NEXT_PUBLIC_APP_VERSION=1.0.0

# Features
NEXT_PUBLIC_ENABLE_BENGALI=true
NEXT_PUBLIC_ENABLE_VOICE=false
NEXT_PUBLIC_MAX_FILE_SIZE=10485760
```

### 3. Run Development Server

```bash
npm run dev
```

The application starts at **http://localhost:3000**

### 4. Build for Production

```bash
npm run build
npm start
```

## Project Structure

```
services/frontend/
├── app/                        # Next.js App Router
│   ├── (auth)/                 # Auth route group
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/            # Dashboard route group
│   │   ├── chat/
│   │   ├── search/
│   │   └── profile/
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Home page
│   └── globals.css             # Global styles
│
├── components/                 # React components
│   ├── ui/                     # Reusable UI components
│   ├── auth/                   # Auth-related components
│   ├── chat/                   # Chat components
│   └── search/                 # Search components
│
├── lib/                        # Utilities and configs
│   ├── api/                    # API layer
│   │   ├── client.ts           # Axios client setup
│   │   ├── services/           # Service functions
│   │   │   ├── auth.service.ts
│   │   │   ├── user.service.ts
│   │   │   ├── chat.service.ts
│   │   │   └── search.service.ts
│   │   └── index.ts
│   ├── config.ts               # App configuration
│   └── utils.ts                # Helper functions
│
├── hooks/                      # Custom React hooks
│   ├── useAuth.ts
│   ├── useChat.ts
│   └── useSearch.ts
│
├── store/                      # Zustand state stores
│   ├── authStore.ts
│   └── uiStore.ts
│
├── types/                      # TypeScript types
│   ├── auth.ts
│   └── api.ts
│
├── messages/                   # i18n translations
│   ├── en.json                 # English
│   └── bn.json                 # Bengali
│
├── public/                     # Static assets
│
├── .env.example                # Environment template
├── .env.local                  # Local environment (gitignored)
├── package.json                # Dependencies
└── README.md                   # This file
```

## API Integration Details

### Gateway Client Setup

```typescript
// lib/api/client.ts
import axios from 'axios';

const gatewayClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_GATEWAY_URL,
  timeout: 30000,
});

// Add JWT token to requests
gatewayClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 and refresh token
gatewayClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Automatic token refresh
      await refreshToken();
      return gatewayClient(error.config);
    }
    return Promise.reject(error);
  }
);
```

### Authentication Flow

```typescript
// Login
const response = await gatewayClient.post('/api/auth/login', {
  username,
  password,
});
tokenManager.setTokens(response.data.accessToken, response.data.refreshToken);

// Register
const response = await gatewayClient.post('/api/auth/register', userData);

// Logout
tokenManager.clearTokens();
```

### Chat/Q&A Integration

```typescript
// Send chat message (routes through gateway to RAG service)
const response = await gatewayClient.post('/api/rag/qa', {
  question: 'What are property rights in Bangladesh?',
});

// Search legal documents
const response = await gatewayClient.post('/api/rag/search', {
  query: 'property law',
  limit: 5,
});
```

## Configuration Reference

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `NEXT_PUBLIC_GATEWAY_URL` | Gateway API URL | http://localhost:8081 | Yes |
| `NEXT_PUBLIC_RAG_URL` | RAG service URL | http://localhost:8000 | No |
| `NEXT_PUBLIC_APP_NAME` | Application name | BD Law Assistant | No |
| `NEXT_PUBLIC_ENABLE_BENGALI` | Enable Bengali | true | No |

### Token Storage

Tokens are stored in HTTP-only cookies:

```typescript
tokenKeys: {
  access: 'bd_law_access_token',    // 1 day expiry
  refresh: 'bd_law_refresh_token',  // 7 days expiry
  user: 'bd_law_user',              // User data
}
```

## Development

### Adding New Pages

```bash
# Create new route
mkdir -p app/new-route
touch app/new-route/page.tsx
```

### Adding New API Service

```typescript
// lib/api/services/new-service.ts
import { gatewayClient } from '../client';

export const newService = {
  getData: async () => {
    const response = await gatewayClient.get('/api/new/data');
    return response.data;
  },
};
```

## Internationalization (i18n)

### Language Files

```json
// messages/en.json
{
  "auth": {
    "login": "Login",
    "register": "Register"
  }
}
```

```json
// messages/bn.json
{
  "auth": {
    "login": "লগইন",
    "register": "নিবন্ধন"
  }
}
```

### Usage in Components

```typescript
import { useTranslations } from 'next-intl';

export default function LoginPage() {
  const t = useTranslations('auth');
  return <button>{t('login')}</button>;
}
```

## Testing

### Manual Testing

```bash
# Start all services
# 1. Gateway (port 8081)
# 2. RAG Service (port 8000)
# 3. Frontend (port 3000)

# Test authentication
# Visit http://localhost:3000/login

# Test search
# Visit http://localhost:3000/dashboard/search
```

### Build Test

```bash
npm run build
npm run lint
```

## Deployment

### Docker

```bash
# Build image
docker build -t bd-law-frontend:1.0.0 .

# Run container
docker run -d \
  -p 3000:3000 \
  -e NEXT_PUBLIC_GATEWAY_URL=http://gateway:8081 \
  --name frontend \
  bd-law-frontend:1.0.0
```

## Troubleshooting

### Common Issues

**API Connection Refused**
```bash
# Check gateway is running
curl http://localhost:8081/actuator/health

# Verify NEXT_PUBLIC_GATEWAY_URL in .env.local
```

**Authentication Fails**
```bash
# Clear cookies in DevTools
# Application > Cookies > Clear All

# Check token exists: bd_law_access_token
```

**Build Errors**
```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

**Port Already in Use**
```bash
# Kill process on port 3000
npx kill-port 3000

# Or use different port
PORT=3002 npm run dev
```

## Security

- **Token Storage**: Secure cookies with `httpOnly`, `secure`, `sameSite` flags
- **XSS Protection**: React automatically escapes content
- **Environment Variables**: Never commit `.env.local`
- **HTTPS**: Always use HTTPS in production

## License

Apache License 2.0

## Support

- **Gateway API**: `services/gateway/README.md`
- **RAG Service**: `services/rag_service/README.md`

---

**Version**: 1.0.0
**Status**: Operational
**Last Updated**: 2025-10-02
