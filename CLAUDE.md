# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EMOGUCHI (エモグチ) is a real-time voice-based emotion guessing game where players act out emotions and guess what others are expressing. The system uses no persistent storage - everything runs in memory for lightweight, session-based gameplay.

## Architecture

### Frontend (Next.js + TypeScript)
- **Framework**: Next.js with App Router
- **Styling**: Tailwind CSS 
- **State Management**: Zustand
- **Real-time Communication**: Socket.IO Client
- **Audio Processing**: MediaRecorder API, Web Audio API

### Backend (FastAPI + Python)
- **Framework**: FastAPI with Socket.IO integration
- **Server**: Uvicorn (ASGI)
- **Models**: Pydantic v2 for data validation
- **LLM Integration**: OpenAI API for dialogue generation
- **Storage**: In-memory dictionaries (no database)

### Project Structure
```
frontend/              # Next.js + TypeScript
├── app/               # App Router routes
├── components/        # UI components
├── hooks/             # Custom hooks (useSocket, etc.)
├── stores/            # Zustand state management
├── types/             # TypeScript type definitions
└── socket/            # Socket.IO connection logic

backend/               # FastAPI server
├── main.py            # ASGI entry point
├── api/               # REST API endpoints
├── sockets/           # WebSocket (Socket.IO) logic
├── models/            # Pydantic models
├── services/          # Business logic
└── config.py          # Configuration
```

## Game Flow

1. **Setup Phase**: LLM generates dialogue, emotion selected via dropdown
2. **Speaker Phase**: Current speaker gets dialogue + emotion privately
3. **Performance Phase**: Speaker reads dialogue aloud (emotion hidden from listeners)
4. **Voting Phase**: Listeners vote on the emotion (4 or 8 choices)
5. **Results Phase**: Reveal correct emotion and scoring

## Emotions System

- **Basic Mode**: 8 fundamental emotions (Joy, Anger, Sadness, etc.)
- **Advanced Mode**: 24 complex emotions (combinations of basic emotions)

## Development Commands

Since this project is in planning phase, development commands will be established when the codebase is implemented. Expected commands based on the tech stack:

**Frontend (Next.js)**:
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm run type-check` - TypeScript type checking

**Backend (FastAPI)**:
- `uvicorn main:app --reload` - Start development server
- `python3 -m pytest` - Run tests (if implemented)

**Full Stack**:
- `docker-compose up` - Start full development environment

## Key Implementation Notes

- **No Database**: All state managed in memory using Python dictionaries
- **Real-time**: Heavy use of WebSocket for game synchronization
- **Audio Handling**: Client-side recording with MediaRecorder, Socket.IO for transmission
- **LLM Integration**: OpenAI API for dynamic dialogue generation
- **Extensibility**: Architecture designed for future database integration via StateStore abstraction

## API Structure

- **REST API**: `/api/v1/` for room management and LLM prefetching
- **WebSocket**: Socket.IO for real-time game events
- **Authentication**: Host tokens for room control, debug tokens for development
- **Error Codes**: EMO-xxx format for consistent error handling

## Testing Approach

- **Frontend**: Vitest for unit tests, Playwright for E2E
- **Backend**: pytest for API testing
- **Integration**: Socket.IO testing for real-time scenarios

## Playwright MCP使用ルール

### 絶対的な禁止事項

1. **いかなる形式のコード実行も禁止**

   - Python、JavaScript、Bash等でのブラウザ操作
   - MCPツールを調査するためのコード実行
   - subprocessやコマンド実行によるアプローチ

2. **利用可能なのはMCPツールの直接呼び出しのみ**

   - playwright:browser_navigate
   - playwright:browser_screenshot
   - 他のPlaywright MCPツール

3. **エラー時は即座に報告**
   - 回避策を探さない
   - 代替手段を実行しない
   - エラーメッセージをそのまま伝える