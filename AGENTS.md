# LocusVision — AI Coding Agent Guide

This document provides essential information for AI coding agents working on the LocusVision codebase.

---

## Project Overview

**LocusVision** is an open-source, high-performance video analytics engine designed for the Raspberry Pi 5 (8GB). It parses reality in real-time—turning video feeds into structured data, searchable events, and actionable insights. The project is built to be local-first, privacy-centric, and highly optimized for edge deployment.

### Key Characteristics

- **Target Platform**: Raspberry Pi 5 (8GB RAM), Raspberry Pi OS 64-bit
- **Architecture**: Full-stack application with SvelteKit frontend and FastAPI backend
- **AI/ML**: ONNX Runtime with YOLO models (supports INT8/FP16 quantization)
- **Database**: SQLite (async via aiosqlite) for primary data, DuckDB for analytics
- **Authentication**: JWT with access/refresh tokens, Argon2id password hashing

---

## Technology Stack

| Category | Technology |
|----------|------------|
| Frontend | SvelteKit 2, TypeScript, Svelte 5 |
| Styling | Tailwind CSS 4 |
| UI Components | shadcn-svelte, bits-ui, mode-watcher |
| Backend | FastAPI, Python 3.11+ |
| Database | SQLite (aiosqlite), DuckDB |
| AI / Vision | ONNX Runtime, ByteTrack (supervision), OpenCV |
| Auth | JWT (access + refresh tokens), Argon2id |
| Build | Vite |
| Testing | Vitest (frontend), pytest (backend) |
| Linting | ESLint + Prettier |

---

## Repository Structure

```text
locusvision/
├── backend/                   # FastAPI backend & analytics engine
│   ├── routers/               # API endpoints
│   │   ├── auth.py            # Authentication (login, signup, refresh)
│   │   ├── cameras.py         # Camera CRUD and configuration
│   │   ├── livestream.py      # MJPEG streaming and SSE telemetry
│   │   ├── video_processing.py# Video upload and job queue
│   │   ├── analytics.py       # Analytics queries and events
│   │   ├── metrics.py         # System metrics
│   │   ├── system.py          # Storage and system health
│   │   ├── settings.py        # User settings and admin config
│   │   └── models.py          # ML model discovery
│   ├── services/              # Core business logic
│   │   ├── analytics_engine.py# Zone counting, line crossing detection
│   │   ├── job_queue.py       # Video processing queue (SQLite-backed)
│   │   ├── livestream_manager.py# Per-camera inference (multiprocessing)
│   │   ├── onnx_detector.py   # ONNX Runtime YOLO inference
│   │   ├── metrics_collector.py# Background metrics aggregation
│   │   ├── downsampler.py     # Metrics data archival
│   │   ├── archiver.py        # Cleanup old processed videos
│   │   ├── duckdb_client.py   # DuckDB connection manager
│   │   └── model_manager.py   # ONNX model discovery
│   ├── scripts/               # Model export and optimization
│   │   └── export_model.py    # Export YOLO to ONNX with quantization
│   ├── tests/                 # Backend tests
│   ├── main.py                # FastAPI application entry point
│   ├── database.py            # Async SQLite configuration
│   ├── auth.py                # JWT and password hashing utilities
│   ├── config.py              # Pydantic-settings configuration
│   ├── models.py              # Pydantic request/response models
│   └── requirements.txt       # Python dependencies
├── src/                       # SvelteKit frontend application
│   ├── lib/                   # Shared components and utilities
│   │   ├── components/        # Svelte components
│   │   │   ├── ui/            # shadcn-svelte UI components
│   │   │   ├── livestream/    # Livestream-specific components
│   │   │   ├── video-analytics/# Video upload and job components
│   │   │   └── create/        # Camera creation components (drawing canvas)
│   │   ├── hooks/             # Custom Svelte hooks (is-mobile.svelte.ts)
│   │   ├── stores/            # Svelte 5 runes-based stores
│   │   ├── utils.ts           # Utility functions (cn, type helpers)
│   │   └── coco-classes.ts    # COCO dataset class names
│   ├── routes/                # SvelteKit routes
│   │   ├── (app)/             # Authenticated routes (protected)
│   │   │   ├── +page.svelte   # Dashboard
│   │   │   ├── livestream/    # Live camera streams
│   │   │   ├── video-analytics/# Video upload and processing
│   │   │   ├── analytics/     # Analytics dashboard
│   │   │   ├── system/        # System monitoring
│   │   │   ├── settings/      # User settings
│   │   │   └── create/[taskId]/# Camera/zone creation
│   │   ├── (auth)/            # Public auth routes
│   │   │   ├── login/
│   │   │   ├── signup/
│   │   │   └── get-started/   # Initial setup
│   │   ├── +layout.svelte     # Root layout
│   │   └── layout.css         # Global styles and CSS variables
│   ├── hooks.server.ts        # Server-side auth hook (JWT validation)
│   └── app.d.ts               # TypeScript declarations
├── scripts/                   # Build and benchmark scripts
│   └── benchmark.sh           # Performance benchmarking
├── static/                    # Static assets
├── data/                      # Runtime data (SQLite, uploads, processed)
├── package.json               # Node.js dependencies
├── svelte.config.js           # SvelteKit configuration
├── vite.config.ts             # Vite configuration
├── tsconfig.json              # TypeScript configuration
├── eslint.config.js           # ESLint configuration
├── .prettierrc                # Prettier configuration
├── components.json            # shadcn-svelte configuration
└── pnpm-workspace.yaml        # pnpm workspace
```

---

## Build and Development Commands

### Development Server

```bash
# Start fullstack dev server (frontend + backend concurrently)
pnpm dev

# Start frontend only (Vite dev server on port 5173)
pnpm dev:frontend

# Start backend only (FastAPI/uvicorn on port 8000 with reload)
pnpm dev:backend
```

### Building and Previewing

```bash
# Production build (outputs to dist/)
pnpm build

# Preview production build
pnpm preview
```

### Code Quality

```bash
# Lint all files (ESLint + Prettier check)
pnpm lint

# Format all files with Prettier
pnpm format

# Type-check Svelte files
pnpm check

# Type-check in watch mode
pnpm check:watch
```

### Testing

```bash
# Frontend unit tests (Vitest, single run)
pnpm test

# Frontend tests in watch mode
pnpm test:unit

# Run a single frontend test file
pnpm test -- src/path/to/file.test.ts

# Backend tests (pytest) — requires venv: source backend/.venv/bin/activate
cd backend && pytest

# Run a single backend test file
cd backend && pytest tests/test_analytics_engine.py

# Run a single backend test function
cd backend && pytest tests/test_analytics_engine.py::test_function -v
```

### Benchmarking

```bash
# Run build size & performance benchmark
pnpm benchmark
```

---

## Frontend-Backend Communication

There is **no Vite proxy** — the frontend calls the backend directly at `http://localhost:8000`. Both servers run independently on different ports (5173 for frontend, 8000 for backend). CORS is configured in `backend/config.py` for these origins.

API calls use native `fetch` (no axios or wrapper library). Server-side calls in `hooks.server.ts` and `+page.ts` load functions hit the backend directly. Client-side calls in components use the same pattern.

Interactive API docs are available at `http://localhost:8000/docs`.

---

## Code Style Guidelines

### Formatting (Prettier)

- **Tabs** for indentation
- **Single quotes**
- **No trailing commas**
- **100 character** print width
- Svelte files use the `svelte` parser
- Tailwind class sorting is automatic via `prettier-plugin-tailwindcss`

ESLint uses flat config format (ESLint 9). `no-undef` is off (TypeScript handles it).

### Frontend (SvelteKit + TypeScript)

#### Svelte 5 Runes

Use Svelte 5 runes syntax. **Avoid legacy `$:` reactive statements.**

```svelte
<script>
  // ✅ Correct - Svelte 5 runes
  let count = $state(0);
  let doubled = $derived(count * 2);

  function increment() {
    count++;
  }
</script>
```

#### Styling with Tailwind CSS

- Use Tailwind CSS utility classes
- Use `cn()` utility from `$lib/utils.ts` for conditional classes
- CSS variables for theming are defined in `src/routes/layout.css`
- Follow shadcn-svelte patterns for component styling

```svelte
<script>
  import { cn } from '$lib/utils';

  let { class: className, variant = 'default' } = $props();
</script>

<div class={cn('base-classes', variant === 'default' && 'default-classes', className)}>
</div>
```

#### Component Imports

Use the `$lib` alias for imports:

```typescript
// ✅ Correct
import Button from '$lib/components/ui/button/button.svelte';
import { cn } from '$lib/utils';

// ❌ Avoid relative imports like '../../../lib/components/...'
```

#### TypeScript Types

- Use explicit types for function parameters and return values
- Define interfaces for component props
- Use `$props()` rune for component props in Svelte 5
- User type defined in `src/app.d.ts`: `{ id: number; email: string; name: string; role: 'admin' | 'viewer' } | null`

```svelte
<script lang="ts">
  interface Props {
    title: string;
    count?: number;
  }

  let { title, count = 0 }: Props = $props();
</script>
```

### Backend (FastAPI + Python)

#### Async Patterns

- All database operations must be async (using `aiosqlite`)
- Use FastAPI dependency injection for common patterns
- Background workers use threading (job queue) or multiprocessing (livestream inference)

```python
# ✅ Correct - async database operations
async def get_user(db: aiosqlite.Connection, user_id: int) -> User | None:
    cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = await cursor.fetchone()
    return User(**row) if row else None
```

#### Environment Variables

All environment variables use `LOCUS_` prefix and are defined in `backend/config.py` (reads `.env` from `backend/`):

```python
from config import settings

# Access via settings object
secret = settings.jwt_secret
db_path = settings.database_path
```

#### Router Organization

All routers use `APIRouter(prefix="/api/...", tags=[...])` and are mounted in `main.py`:

```python
# routers/cameras.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/cameras", tags=["cameras"])

@router.get("/")
async def list_cameras():
    ...
```

---

## Testing Details

### Frontend Testing

- Tests are located alongside components or in `src/**/*.test.ts`
- Uses Vitest with `node` environment (configured in `vite.config.ts`)
- Test files: `*.test.ts` or `*.spec.ts`

### Backend Testing

- Tests are in `backend/tests/`
- Uses pytest with `unittest.mock` (patch, MagicMock) for mocking
- Requires venv activation: `source backend/.venv/bin/activate`

---

## Authentication Flow

### Frontend (hooks.server.ts)

1. All routes except `/login`, `/signup`, `/get-started`, `/logout` require authentication
2. JWT access token stored in HttpOnly cookie (`maxAge: 15 minutes`)
3. Refresh token stored in HttpOnly cookie (`maxAge: 7 days`)
4. Server hook validates tokens against FastAPI backend (`/api/auth/me`)
5. Auto-refreshes expired access tokens using refresh token
6. User data attached to `event.locals.user` and available in all route loaders

### Backend (routers/auth.py)

1. Login endpoint validates credentials and returns access/refresh tokens
2. Access tokens expire after 15 minutes
3. Refresh tokens expire after 7 days
4. Tokens stored in HttpOnly cookies (`secure: false` in dev, should be `true` in production)
5. Rate limiting: 5 attempts per 5-minute window per IP (in-memory tracking)

---

## Key Development Conventions

### Route Groups

- `(app)/` — Authenticated routes with sidebar layout
- `(auth)/` — Public routes (login, signup) without sidebar

### Database

- SQLite uses WAL mode and foreign keys (`PRAGMA journal_mode=WAL`, `PRAGMA foreign_keys=ON`)
- Database file location: `backend/data/locusvision.db`

### Database Migrations

The project uses inline migrations in `backend/database.py` `init_db()` (no Alembic). When adding new columns:

1. Add column to CREATE TABLE statement
2. Add migration in the migrations dict for existing databases

### Model Management

ONNX models are stored in `data/models/` and discovered dynamically:

- Models are validated on startup by `model_manager.py`
- Users can select models via the Camera Settings UI
- Export quantized models: `python backend/scripts/export_model.py yolo11n --int8`
- Argon2id parameters are tuned for Raspberry Pi 5 constrained memory

---

## Performance Considerations

### Raspberry Pi 5 Optimization

1. **Use INT8 quantized models** — 2-3x performance improvement
2. **Enable motion detection pre-filtering** — Reduces unnecessary inference
3. **Adjust inference FPS** — Lower values reduce CPU usage
4. **Mount storage on SSD** — Better I/O for video processing

### Frontend Bundle

- JS/CSS bundles are optimized for size
- Vendor chunk is split from application code
- Use `pnpm benchmark` to verify bundle size

---

## Security Considerations

### Authentication

- JWT tokens with short expiration (15 minutes for access)
- Refresh tokens with longer expiration (7 days)
- Argon2id for password hashing (OWASP 2025 minimum, tuned for Pi 5)
- Rate limiting on login attempts (5 attempts, 5-minute lockout)

### Environment Variables

Create a `.env` file in `backend/` directory:

```env
# Security (generate secure random values for production)
LOCUS_JWT_SECRET=your-secret-key-here

# Database
LOCUS_DATABASE_PATH=./data/locusvision.db
```

### Production Checklist

- Change default JWT secret
- Enable HTTPS and set `secure: true` for cookies in `hooks.server.ts`
- Disable public signup (controlled via admin settings)
- Set up proper CORS origins in `config.py`

---

## Common Tasks

### Adding a New API Endpoint

1. Add route handler in appropriate `backend/routers/*.py` file
2. Add Pydantic models in `backend/models.py` if needed
3. Test with FastAPI docs at `http://localhost:8000/docs`

### Adding a New Frontend Page

1. Create directory in `src/routes/(app)/` for authenticated pages
2. Add `+page.svelte` (and optionally `+page.ts` for load functions)
3. Update sidebar navigation in `src/lib/components/app-sidebar.svelte`

### Adding a UI Component

1. Check if shadcn-svelte has the component: `npx shadcn-svelte@latest add <component>`
2. Custom components go in `src/lib/components/<feature>/`
3. Export from `src/lib/components/ui/<component>/index.ts` for shadcn components

### Adding a Database Table

1. Add CREATE TABLE statement in `backend/database.py` `init_db()` function
2. Add helper functions for CRUD operations
3. Add corresponding Pydantic models in `backend/models.py`
4. Add API endpoints in appropriate router

---

## Troubleshooting

### Common Issues

**Frontend not connecting to backend**
- Check backend is running on port 8000
- Verify CORS origins in `backend/config.py`

**Camera not detected**
- Check camera permissions: `sudo usermod -a -G video $USER`
- Verify with: `v4l2-ctl --list-devices`

**Model loading errors**
- Ensure models are in `./data/models/` directory
- Check ONNX Runtime compatibility with architecture

**Performance issues on Pi**
- Reduce input resolution in camera settings
- Enable INT8 quantization
- Lower the inference FPS target

---

## Resources

- [SvelteKit Docs](https://kit.svelte.dev/docs)
- [Svelte 5 Runes](https://svelte.dev/docs/svelte/what-are-runes)
- [shadcn-svelte](https://www.shadcn-svelte.com/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Tailwind CSS](https://tailwindcss.com/)
