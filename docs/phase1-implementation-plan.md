# Phase 1: Edge Architecture & Analytics Implementation Plan

## Goal Description
Transform the current SQLite/In-Memory based LocusVision engine into a robust, local-first edge architecture utilizing DuckDB for high-performance analytics, and implement the Enhanced Zone, Line, and Object Tracking features.

## Proposed Changes

### 1. Database Infrastructure Setup
#### [NEW] `backend/db/duckdb_client.py`
- Initialize embedded `locus_active.duckdb` connection.
- Create schema definitions for telemetry tables:
  - `zone_events` (timestamp, camera_id, zone_id, event_type, track_id, dwell_time)
  - `line_events` (timestamp, camera_id, line_id, direction, track_id)
  - `object_tracks` (timestamp, camera_id, track_id, class_id, x, y)
- Implement optimized batch-insert functions using `executemany` to handle high-frequency events.

#### [MODIFY] `backend/db/sqlite_client.py`
- Strip out any existing telemetry/metrics schemas.
- Ensure only state schemas exist: `cameras`, `workspaces`, `zones` (polygons), `lines` (coords), `settings`.

### 2. Core Analytics Engine Refactoring
#### [MODIFY] `backend/analytics/engine.py`
- Introduce a `mode` parameter (`live` vs `batch`) to dictate processing strategies.
- Implement an event buffer (e.g., `asyncio.Queue` or a simple list) that flushes to `duckdb_client.py` every N seconds or N events to maximize DuckDB write performance.
- Implement garbage collection for the `live` mode: continuously purge the `active_tracks` dictionary of any IDs that haven't been seen in the last 10 seconds to prevent RAM leaks.

### 3. Enhanced Analytics Modules
#### [NEW] `backend/analytics/zone_analyzer.py`
- Implement robust dwell time calculation logic:
  - **Live Mode:** Send `current_dwell` duration updates to the frontend via WebSockets; trigger `check_capacity_alerts()` on every entry.
  - **Batch Mode:** Record absolute `entry_time` and `exit_time` into DuckDB upon object exit.

#### [NEW] `backend/analytics/line_analyzer.py`
- Implement explicit directional tracking (e.g., Vector A->B vs B->A) based on the object's centroid history crossing the line segment.
- Record `crossing_velocity` estimation based on the last N frames.

#### [NEW] `backend/analytics/trajectory_mapper.py`
- Cache `(x, y)` centroids per `track_id`.
- Function to generate GeoJSON or simplified path coordinate arrays for the frontend to render "spaghetti maps".

### 4. Background Downsampling & Archival
#### [NEW] `backend/tasks/downsampler.py`
- A background worker (using FastAPI's `BackgroundTasks` or APScheduler).
- Runs hourly to execute DuckDB continuous aggregations (e.g., raw tracking steps -> hourly zone counts).
- **Function:** `rollup_hourly_stats()`

#### [NEW] `backend/tasks/archiver.py`
- Runs monthly.
- Executes: `COPY (SELECT * FROM telemetry WHERE timestamp < [LAST_MONTH]) TO 'data/archives/{month}.parquet' (FORMAT PARQUET)`.
- Deletes the exported raw data from `locus_active.duckdb`.

## Verification Plan

### Automated Tests
- **Database Unit Tests:** Validate DuckDB schema creation, verify batch insert performance (>1000 rows/sec).
- **Integration Tests:** Feed a mocked JSON stream of bounding boxes into the `engine.py` and verify events are correctly routed to DuckDB.
- **Archival Tests:** Mock a database with 60-day old data and trigger the `archiver.py`. Verify the `.parquet` file is created and the DuckDB row count drops.

### Manual Verification
- **Live Mode Testing:** Connect to an RTSP stream. Verify memory usage stabilizes over a 1-hour run (proving track garbage collection works). Verify WebSockets push capacity alerts instantly.
- **Batch Mode Testing:** Process a 5-minute `.mp4` video. Verify the final DuckDB tables contain accurate `entry_time` and `exit_time` records for the shoppers in the video. Query the parquet exports using DuckDB CLI.
