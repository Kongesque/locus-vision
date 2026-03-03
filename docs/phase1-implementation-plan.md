# Phase 1: Edge Architecture & Analytics Implementation Plan

## Goal Description
Transform the current purely in-memory, SQLite-backed LocusVision engine into a robust, local-first edge architecture utilizing DuckDB for high-performance analytics, and implement the Enhanced Zone, Line, and Object Tracking features.

## Proposed Changes

### 1. Database Infrastructure Setup
#### [NEW] `backend/services/duckdb_client.py`
- Add `duckdb` and `pyarrow`/`fastparquet` to `backend/requirements.txt`.
- Initialize embedded `locus_active.duckdb` connection.
- Create schema definitions for telemetry tables:
  - `zone_events` (timestamp, camera_id, zone_id, event_type, track_id, dwell_time)
  - `line_events` (timestamp, camera_id, line_id, direction, track_id)
  - `object_tracks` (timestamp, camera_id, track_id, class_id, x, y)
- Implement optimized batch-insert functions using `executemany` to handle high-frequency events.

#### [MODIFY] `backend/database.py`
- Ensure SQLite is purely used for Operational State: `cameras`, `users`, `sessions`, `app_settings`, `video_tasks`.

### 2. Core Analytics Engine Refactoring
#### [MODIFY] `backend/services/analytics_engine.py`
- Refactor to support explicit `live` vs `batch` modes to dictate processing strategies.
- **For `live` mode:**
  - Enforce hard garbage collection: continuously purge the `track_history` and `crossed_objects` of any IDs that haven't been seen recently to prevent memory leaks in continuous 24/7 operation.
  - Implement immediate Dwell Time calculations.
  - Send `current_dwell` and Capacity Alerts (e.g., >80% capacity) via websocket events.
  - Implement instant directional anomaly alerting (wrong-way traversal).
- **For `batch` mode:**
  - Precision timestamp extraction for `entry_timestamp` and `exit_timestamp`.
  - Record absolute average dwell times.
  - Generate "Spaghetti Maps" (Flow Diagrams) and zone velocity calculations across the whole video.

#### [MODIFY] `backend/services/livestream_manager.py`
- Integrate an event flushing buffer that sends AI inference events to DuckDB for persistence, alongside the current SSE broadcast.

#### [MODIFY] `backend/services/job_queue.py`
- Update batch processor to write complete analytical data (like precision timestamps and spaghetti maps) into DuckDB. 

### 3. Background Downsampling & Archival
#### [NEW] `backend/services/downsampler.py`
- A background worker (using FastAPI's `BackgroundTasks` or APScheduler).
- Runs hourly/nightly to execute DuckDB continuous aggregations (e.g., raw tracking steps -> hourly zone counts).

#### [NEW] `backend/services/archiver.py`
- Runs monthly.
- Executes: `COPY (SELECT * FROM telemetry WHERE timestamp < [LAST_MONTH]) TO 'data/archives/{month}.parquet' (FORMAT PARQUET)`.
- Deletes the exported raw data from `locus_active.duckdb` to keep the active database blazing fast.

## Verification Plan

### Automated Tests
- **Database Unit Tests:** Validate DuckDB schema creation, verify batch insert performance (>1000 rows/sec).
- **Integration Tests:** Feed a mocked JSON stream of bounding boxes into `analytics_engine.py` and verify events are correctly routed to DuckDB.
- **Archival Tests:** Mock a database with 60-day old data and trigger `archiver.py`. Verify the `.parquet` file is created and the DuckDB row count drops.

### Manual Verification
- **Live Mode Testing:** Connect to an RTSP stream (via UI or dummy feed). Verify memory usage stabilizes over a 1-hour run (proving track garbage collection works). Verify WebSockets push capacity alerts instantly.
- **Batch Mode Testing:** Process a 5-minute `.mp4` video. Verify the final DuckDB tables contain accurate `entry_time` and `exit_time` records for the objects in the video. Query the parquet exports using DuckDB CLI.
