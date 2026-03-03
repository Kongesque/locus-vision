# LocusVision Technical Specification: Edge Architecture & Phase 1 Analytics 

## Part 1: The Local-First, Edge-Optimized Database Architecture

LocusVision is built on a **local-first, privacy-centric philosophy**. As an edge-native analytics platform, it does not rely on massive, expensive cloud databases (like TimescaleDB clusters or ClickHouse shards). Instead, it uses an immensely powerful embedded database stack capable of storing 1 to 10 years of highly compressed spatial data locally.

### The Embedded Data Stack

1. **SQLite (The Brain - Operational State)**
   - **Role:** Master configuration and state management.
   - **Data:** Camera endpoints, Workspace configurations, Zone Polygons, Line Coordinates, User settings, and Alert configurations.
   - **Why:** Zero-configuration, transactional, and perfect for low-volume, critical application state.

2. **DuckDB (The Engine - Fast Analytics)**
   - **Role:** High-Performance Spatial & Time-Series computation.
   - **Data:** Raw bounding boxes, tracking ID lifecycles, zone entry/exit events, line crossings, and active dwell times (data under 30 days).
   - **Why:** DuckDB runs *inside* the Locus Python process as an embedded columnar OLAP database. It can execute complex analytical group-bys (downsampling) on millions of rows in milliseconds on standard edge hardware (like an Intel NUC or Jetson).

3. **Apache Parquet (The Deep Archive - 10-Year Cold Storage)**
   - **Role:** Ultra-compressed long-term retention.
   - **Data:** Historical telemetry data rolled up daily/monthly.
   - **Why:** Based on a retention schedule, active DuckDB data is continuously aggregated and exported into local `.parquet` files. A year of traffic data compresses down to Megabytes. DuckDB can query hundreds of these local `.parquet` files directly without needing to import them, enabling instant 5-to-10-year historical reports directly from disk.

### The Edge Pipeline

1. **Ingest (Hot):** Inference engine outputs detections -> Batched writing to embedded `locus_active.duckdb`.
2. **Downsample (Warm):** Nightly background tasks summarize raw telemetry (e.g., raw tracking steps become 5-minute zone counts) within DuckDB.
3. **Archive (Cold):** Monthly, the oldest warm data is exported using standard `COPY TO FORMAT PARQUET` to local disk and purged from DuckDB to keep the active file blazing fast.

---

## Part 2: Phase 1 Implementation Plan - Core Analytics Modules

To support multiple deployment modes (Real-Time RTSP vs Pre-recorded Video Batch Analysis), the Analytics modules change their processing strategies dramatically.

### Module 1: Enhanced Zone Analytics
**Structure:** Polygons defined over camera feeds.

* **Livestream (Real-time Focus):**
  - **Priorities:** Low latency, frame-dropping allowed to maintain real-time edge.
  - **Features Application:** Immediate Occupancy counting. Real-time Capacity Alerts calculation (e.g., trigger webhook the millisecond an entry pushes the zone to >80% capacity). Current Dwell Time calculations for immediate Loitering detection.
* **Video Analytics (Batch Focus):**
  - **Priorities:** Complete accuracy, processing every frame (faster or slower than real-time speed).
  - **Features Application:** Precision timestamp extraction (`entry_timestamp`, `exit_timestamp`) stored into the DuckDB telemetry table. Calculation of absolute average dwell times across an entire shift to be rolled up into Parquet reports.

### Module 2: Line Analytics
**Structure:** Bi-directional virtual tripwires.

* **Livestream (Real-time Focus):**
  - **Features Application:** Real-time gatekeeping. Immediate dashboard counter ticks upon cross detection. Instant directional anomaly alerting (e.g., detecting wrong-way traversal in an exit lane).
* **Video Analytics (Batch Focus):**
  - **Features Application:** Deep trend analysis. Processing an entire day's .mp4 to calculate absolute flow rates, line crossing velocities, and definitive peak crossing hours. All events are batched intoDuckDB for macro-hourly aggregations.

### Module 3: Object Tracking & Behavior
**Structure:** ByteTrack object lifecycles merged with detections.

* **Livestream (Real-time Focus):**
  - **State Management:** Highly aggressive memory pruning. "Lost" tracks must be garbage-collected immediately to prevent memory leaks in a 24/7 stream.
  - **Features Application:** Visualizing the immediate trajectory (last 5 seconds) on the Live View matrix to help operators understand current flow direction visually.
* **Video Analytics (Batch Focus):**
  - **State Management:** Tracking IDs persist across the entire video.
  - **Features Application:** Generating complete "Spaghetti Maps" (Flow Diagrams) showing an object's complete lifecycle and movement across the entire space. Calculating exact average velocities per zone based on their start and end points in the video file.
