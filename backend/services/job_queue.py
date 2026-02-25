"""
SQLite-backed video processing job queue.

Runs a single daemon worker thread that processes video tasks sequentially.
Uses the existing video_tasks table for state, adding progress tracking.
Crash-resilient: on startup, any 'processing' tasks are reset to 'pending'.
"""

import os
import cv2
import time
import json
import sqlite3
import threading
from typing import Optional
from services.analytics_engine import AnalyticsEngine
from config import settings

CACHE_DIR = "data/videos"
os.makedirs(CACHE_DIR, exist_ok=True)


def _dict_factory(cursor, row):
    return {col[0]: row[i] for i, col in enumerate(cursor.description)}


class VideoJobQueue:
    """
    Singleton job queue that processes video analytics tasks one at a time.

    Uses SQLite polling (every 2s) — lightweight enough for Raspberry Pi,
    no external broker needed.
    """

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._current_task_id: Optional[str] = None
        self._db_path = settings.database_path

    # ── Lifecycle ────────────────────────────────────────────

    def start(self):
        """Start the worker thread. Call once during app lifespan startup."""
        if self._running:
            return
        self._running = True
        self._recover_stale_tasks()
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()
        print("[JobQueue] Worker started.")

    def stop(self):
        """Gracefully stop the worker thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("[JobQueue] Worker stopped.")

    # ── Public API ───────────────────────────────────────────

    def get_queue_status(self) -> dict:
        """Return snapshot of current queue state for the API."""
        conn = self._get_conn()
        try:
            processing = None
            if self._current_task_id:
                row = conn.execute(
                    "SELECT id, filename, progress FROM video_tasks WHERE id = ?",
                    (self._current_task_id,),
                ).fetchone()
                if row:
                    processing = {
                        "task_id": row["id"],
                        "filename": row["filename"],
                        "progress": row["progress"],
                    }

            pending_rows = conn.execute(
                "SELECT id, filename FROM video_tasks WHERE status = 'pending' ORDER BY created_at ASC"
            ).fetchall()
            pending = [{"task_id": r["id"], "filename": r["filename"]} for r in pending_rows]

            return {
                "queue_length": len(pending) + (1 if processing else 0),
                "processing": processing,
                "pending": pending,
            }
        finally:
            conn.close()

    # ── Internal ─────────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = _dict_factory
        return conn

    def _recover_stale_tasks(self):
        """Reset any 'processing' tasks back to 'pending' (crash recovery)."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "UPDATE video_tasks SET status = 'pending', progress = 0 WHERE status = 'processing'"
            )
            if cursor.rowcount > 0:
                print(f"[JobQueue] Recovered {cursor.rowcount} stale task(s).")
            conn.commit()
        finally:
            conn.close()

    def _worker_loop(self):
        """Main loop: poll for pending tasks and process them."""
        while self._running:
            task = self._fetch_next_task()
            if task:
                self._process_task(task)
            else:
                # No work — sleep before polling again
                time.sleep(2)

    def _fetch_next_task(self) -> Optional[dict]:
        """Grab the oldest pending task and mark it as processing."""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM video_tasks WHERE status = 'pending' ORDER BY created_at ASC LIMIT 1"
            ).fetchone()
            if not row:
                return None

            conn.execute(
                "UPDATE video_tasks SET status = 'processing', progress = 0 WHERE id = ?",
                (row["id"],),
            )
            conn.commit()
            self._current_task_id = row["id"]
            return row
        finally:
            conn.close()

    def _update_progress(self, task_id: str, progress: int):
        """Write progress (0–100) to the database."""
        conn = self._get_conn()
        try:
            conn.execute(
                "UPDATE video_tasks SET progress = ? WHERE id = ?",
                (min(progress, 100), task_id),
            )
            conn.commit()
        finally:
            conn.close()

    def _complete_task(self, task_id: str, duration_str: str, total_count: int, zone_counts: dict):
        conn = self._get_conn()
        try:
            conn.execute(
                """
                UPDATE video_tasks
                SET status = 'completed',
                    progress = 100,
                    completed_at = datetime('now'),
                    duration = ?,
                    format = 'mp4',
                    total_count = ?,
                    zone_counts = ?
                WHERE id = ?
                """,
                (duration_str, total_count, json.dumps(zone_counts), task_id),
            )
            conn.commit()
        finally:
            conn.close()
            self._current_task_id = None

    def _fail_task(self, task_id: str, error_msg: str):
        conn = self._get_conn()
        try:
            conn.execute(
                "UPDATE video_tasks SET status = 'failed', error_message = ? WHERE id = ?",
                (error_msg, task_id),
            )
            conn.commit()
        finally:
            conn.close()
            self._current_task_id = None

    def _process_task(self, task: dict):
        """Run video analytics on a single task. Mirrors the old process_video_task logic."""
        task_id = task["id"]
        input_path = os.path.join(CACHE_DIR, f"input_{task_id}.mp4")
        output_path = os.path.join(CACHE_DIR, f"output_{task_id}.mp4")
        model_name = task.get("model_name") or "yolo11n"

        # Parse zones — stored as JSON string in DB
        zones_raw = task.get("zones") or "[]"
        zones = json.loads(zones_raw) if isinstance(zones_raw, str) else zones_raw

        # Parse classes
        classes_raw = task.get("classes") or "[]"
        full_frame_classes = json.loads(classes_raw) if isinstance(classes_raw, str) else classes_raw

        target_fps = 12

        print(f"[JobQueue] Processing task {task_id} ({task.get('filename', '?')})")

        try:
            engine = AnalyticsEngine(
                model_name=model_name,
                zones=zones,
                full_frame_classes=full_frame_classes,
            )

            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                self._fail_task(task_id, f"Cannot open video file: {input_path}")
                return

            # Video properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration_sec = total_frames / fps if fps > 0 else 0
            duration_str = time.strftime("%H:%M:%S", time.gmtime(duration_sec))

            # Generate thumbnail (middle frame)
            cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
            ret, thumb_frame = cap.read()
            if ret:
                thumb_path = os.path.join(CACHE_DIR, f"thumbnail_{task_id}.jpg")
                cv2.imwrite(thumb_path, thumb_frame)
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

            # Calculate frame skipping
            new_fps = min(fps, target_fps)
            skip_interval = max(1, int(fps / new_fps))

            # Output setup
            fourcc = cv2.VideoWriter_fourcc(*"avc1")
            out = cv2.VideoWriter(output_path, fourcc, new_fps, (width, height))

            # Analytical data for JSON export
            analytical_data = {
                "task_id": task_id,
                "filename": task.get("filename", "unknown"),
                "model_name": model_name,
                "fps": new_fps,
                "zones": zones,
                "frames": [],
            }

            frame_count = 0
            frames_to_process = total_frames // skip_interval if skip_interval > 0 else total_frames
            processed_frames = 0
            start_time = time.time()
            last_progress_update = 0
            result = None

            while cap.isOpened() and self._running:
                success, frame = cap.read()
                if not success:
                    break

                frame_count += 1
                if frame_count % skip_interval != 0:
                    continue

                processed_frames += 1
                result = engine.process_frame(frame)
                engine.draw_annotations(frame, result)
                out.write(frame)

                # Store per-frame data
                timestamp = frame_count / fps
                analytical_data["frames"].append(
                    {
                        "timestamp": round(timestamp, 2),
                        "boxes": result.boxes,
                        "current_total_count": result.total_count,
                        "current_zone_counts": result.zone_counts,
                    }
                )

                # Update progress every ~2% or at least every 30 processed frames
                progress = int((processed_frames / max(frames_to_process, 1)) * 100)
                if progress - last_progress_update >= 2 or processed_frames % 30 == 0:
                    self._update_progress(task_id, progress)
                    last_progress_update = progress

            cap.release()
            out.release()

            # Check if we were stopped mid-processing
            if not self._running:
                print(f"[JobQueue] Task {task_id} interrupted by shutdown.")
                # Reset to pending so it gets picked up on next start
                conn = self._get_conn()
                try:
                    conn.execute(
                        "UPDATE video_tasks SET status = 'pending', progress = 0 WHERE id = ?",
                        (task_id,),
                    )
                    conn.commit()
                finally:
                    conn.close()
                    self._current_task_id = None
                return

            # Save analytical data to JSON
            data_path = os.path.join(CACHE_DIR, f"data_{task_id}.json")
            with open(data_path, "w") as f:
                json.dump(analytical_data, f)

            # Cleanup input file
            if os.path.exists(input_path):
                os.remove(input_path)

            elapsed = time.time() - start_time
            print(f"[JobQueue] Task {task_id} completed in {elapsed:.1f}s")

            final_count = result.total_count if result else 0
            final_zone_counts = result.zone_counts if result else {}
            self._complete_task(task_id, duration_str, final_count, final_zone_counts)

        except Exception as e:
            print(f"[JobQueue] Task {task_id} failed: {e}")
            self._fail_task(task_id, str(e))


# ── Module-level singleton ───────────────────────────────────
job_queue = VideoJobQueue()
