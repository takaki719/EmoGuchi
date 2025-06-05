# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EmoGuchi is a real-time multiplayer voice emotion guessing game with a Next.js frontend and FastAPI backend. Players join rooms where one person speaks a phrase with emotion while others vote on the perceived emotion.

## Development Commands

### Frontend (Next.js)
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev        # Start development server (with Turbopack)
npm run build      # Production build
npm run lint       # ESLint
```

### Backend (FastAPI)
```bash
pip install fastapi "python-socketio[asgi]" uvicorn
uvicorn backend.main:app --reload    # Start development server
```

## Architecture

### Communication Pattern
- **REST API** (`/api/v1/`): Room management, phrase prefetching
- **WebSocket** (`/ws`): Real-time game events via Socket.IO
- **State Management**: Zustand store (frontend) + in-memory rooms dict (backend)

### Key Socket Events
- `join_room`: Player joins with roomId + playerName
- `round_start`: Begin round with phrase + target emotion
- `submit_vote`: Submit emotion vote (emotionId)
- `round_result`: Broadcast scores and results

### Authentication
- **Host Token**: Bearer token for room management operations
- **Debug Token**: Development access to `/api/v1/debug/rooms`
- **No Player Auth**: Players join with just a name

### Game Mechanics
- **Basic Mode**: 8 primary emotions, **Advanced Mode**: 24 complex emotions
- **Vote Types**: 4-choice or 8-choice emotion selection
- **Scoring**: +1 for speaker per correct guess, +1 for listener if correct
- **Phrase Generation**: OpenAI integration with fallback phrases

## Key Files

### Frontend
- `src/app/page.tsx`: Main game orchestration
- `src/hooks/useSocket.ts`: Socket.IO connection management
- `src/stores/useRoomStore.ts`: Zustand state management
- `src/components/`: Game UI components (Lobby, VoteButtons, Results)

### Backend
- `backend/main.py`: FastAPI app with REST endpoints
- `backend/sockets/room.py`: Socket.IO event handlers
- `backend/services/prefetch.py`: OpenAI phrase generation

## Development Notes

- Frontend runs on localhost:3000, backend on localhost:8000
- All game state is in-memory (no database)
- CORS configured for localhost:3000 and emoguchi.vercel.app
- Socket.IO path is `/ws`
- Use TypeScript interfaces in `src/types/index.ts` for type safety