# BD Law Assistant - Frontend Service

A modern, responsive web application built with Next.js 15 and React 19, providing an intuitive interface for Bangladesh legal document search and AI-powered legal assistance.

## 🚀 Technology Stack

- **Framework**: Next.js 15.5.3 (App Router)
- **UI Library**: React 19.1.0
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 4
- **State Management**: Zustand 5.0.8
- **Form Handling**: React Hook Form 7.63.0 + Zod 4.1.9
- **HTTP Client**: Axios 1.12.2
- **Internationalization**: next-intl 4.3.9
- **UI Components**: Lucide React 0.544.0
- **Date Handling**: date-fns 4.1.0

## ✨ Key Features

### Authentication & Authorization
- JWT-based authentication with access and refresh tokens
- Automatic token refresh for seamless UX
- Protected routes with middleware
- Secure cookie management

### User Dashboard & Analytics
- Real-time usage statistics
- Activity timeline
- Daily/weekly insights
- Bookmark management

### Legal Search
- AI-powered semantic search
- Beautiful results UI
- Advanced filters
- Type-based search

### Chat & Q&A
- AI legal assistant
- Natural language questions
- Conversation history
- Source attribution

### Bookmarks
- Backend-synced bookmarks
- Folder organization
- Tag management
- Search within bookmarks

## 🔧 Environment Variables

```env
NEXT_PUBLIC_GATEWAY_URL=http://localhost:8081
NEXT_PUBLIC_APP_NAME=BD Law Assistant
```

## 📦 Installation

```bash
cd services/frontend
npm install
cp .env.example .env.local
npm run dev
```

## 🏃 Running

```bash
# Development
npm run dev

# Production
npm run build
npm start
```

Access at `http://localhost:3000`

---

**Version**: 1.0.0
**Status**: ✅ Production Ready
**Last Updated**: 2025-10-05
