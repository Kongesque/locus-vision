# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development
- `pnpm dev` - Start fullstack dev server (frontend + backend concurrently)
- `pnpm dev:frontend` - Start frontend only (Vite dev server on port 5173)
- `pnpm dev:backend` - Start backend only (FastAPI/uvicorn on port 8000 with reload)
- `pnpm build` - Production build (outputs to `dist/`)
- `pnpm preview` - Preview production build

### Testing
- `pnpm test` - Run all unit tests (Vitest with --run)
- `pnpm test:unit` - Run Vitest in watch mode
- `cd backend && pytest` - Run backend tests

### Code Quality
- `pnpm lint` - ESLint + Prettier check
- `pnpm format` - Format all files with Prettier
- `pnpm check` - Type-check Svelte files with svelte-check
- `pnpm check:watch` - Type-check in watch mode

### Other
- `pnpm benchmark` - Run build size & performance benchmark

## High-Level Architecture

### Frontend (SvelteKit 5 + TypeScript)

**Authentication Flow**
- Authentication is handled in `src/hooks.server.ts` via JWT access/refresh tokens stored in HttpOnly cookies
- All routes except `/login`, `/signup`, `/get-started`, `/logout` require authentication
- The hook validates tokens against the FastAPI backend (`/api/auth/me`) and auto-refreshes expired access tokens
- User data is attached to `event.locals.user` and available in all route loaders

**Route Structure**
- `src/routes/(app)/` - Authenticated application routes (livestream, video-analytics, analytics, settings, system)
- `src/routes/(auth)/` - Public authentication routes (login, signup, get-started)
- `src/routes/+layout.svelte` - Root layout with global styles

**Component Architecture**
- UI components use shadcn-svelte (installed in `src/lib/components/ui/`) with bits-ui primitives
- Custom components are organized by feature: `livestream/`, `video-analytics/`, `create/`
- Svelte 5 runes (`$state`, `$derived`) are used throughout - avoid legacy `$:` reactive statements
- Styling uses Tailwind CSS 4 with CSS variables for theming (defined in `src/routes/layout.css`)
- Component aliases: `$lib/components`, `$lib/components/ui`, `$lib/hooks`

**State Management**
- Svelte 5 runes-based stores in `src/lib/stores/` (e.g., `video.svelte.ts`)
- Prefer local component state with props over global stores when possible

### Backend (FastAPI + Python)

**Application Structure**
- `main.py` - FastAPI app factory with lifespan management (starts/stops background workers)
- `config.py` - Pydantic-settings configuration (env vars prefixed with `LOCUS_`)
- `database.py` - Async SQLite (aiosqlite) database initialization and connection management
- `auth.py` - JWT token utilities and Argon2id password hashing
- `models.py` - Pydantic request/response models

**Router Organization**
- `routers/auth.py` - Login, signup, token refresh, user management
- `routers/cameras.py` - Camera CRUD and configuration
- `routers/livestream.py` - MJPEG streaming and SSE telemetry endpoints
- `routers/video_processing.py` - Video upload and job queue management
- `routers/analytics.py` - Analytics queries and event retrieval
- `routers/metrics.py` - System metrics collection endpoint
- `routers/system.py` - Storage management and system health
- `routers/settings.py` - User settings and admin configuration
- `routers/models.py` - ML model discovery and management

**Background Services**
All services are singletons started/stopped in `main.py` lifespan:

- `services/job_queue.py` - SQLite-backed video processing queue with single worker thread. Processes videos sequentially using `AnalyticsEngine`, updates progress in DB. Crash-resilient (resets stale tasks on startup).
- `services/analytics_engine.py` - Stateful per-session engine wrapping ONNX detector with ByteTracker. Handles zone-based counting, line crossing detection (vector cross-product), and event generation. Used by both live streams and video processing.
- `services/livestream_manager.py` - Manages per-camera inference loops (multiprocessing), MJPEG streaming, and SSE telemetry. Each camera runs in isolated process with its own `AnalyticsEngine` instance.
- `services/onnx_detector.py` - ONNX Runtime YOLO inference with NMS. Supports FP16/INT8 quantized models. Dynamic model loading from `data/models/`.
- `services/metrics_collector.py` - Background metrics aggregation (CPU, memory, FPS, detection counts) written to SQLite for time-series queries.
- `services/downsampler.py` - Archives old high-frequency metrics data.
- `services/archiver.py` - Cleans up old processed videos and orphaned files.
- `services/duckdb_client.py` - DuckDB connection manager for analytics queries (Parquet output).
- `services/model_manager.py` - Discovers and validates ONNX models in `data/models/` directory.

**Database Architecture**
- SQLite (aiosqlite) for primary data: users, cameras, video tasks, events, sessions, metrics
- DuckDB for analytics: queries against event data with Parquet export capability
- Database file location: `backend/data/locusvision.db`

**AI/Vision Pipeline**
1. **Detection**: ONNX Runtime with YOLO models (supports FP16/INT8 quantization)
2. **Tracking**: ByteTrack (via supervision library) per-camera instances prevent ID collision
3. **Analytics**: Zone-based counting with polygon containment, directional line crossing (A→B, B→A, both)
4. **Events**: Zone entries/exits, line crossings, track lifecycle events written to DuckDB for analytics

**Key Conventions**
- All database operations are async (aiosqlite)
- FastAPI dependency injection for common patterns (get_current_user, get_db)
- Background workers use threading (job queue) or multiprocessing (livestream inference)
- Environment variables use `LOCUS_` prefix (see `config.py`)
