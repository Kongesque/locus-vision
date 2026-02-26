"""
Camera analytics worker.

Two modes:
1. RTSP mode  – A background thread pulls frames via OpenCV and broadcasts YOLO results.
2. Webcam mode – The browser sends JPEG frames over the WebSocket and we process them inline.

Both modes now use the shared AnalyticsEngine for zone-aware counting.
"""
import asyncio
import threading
import cv2
import json
import time
import sqlite3
import os
import numpy as np
from services.analytics_engine import AnalyticsEngine

from routers.cameras import active_connections
from config import settings

MODELS_DIR = "data/models"
os.makedirs(MODELS_DIR, exist_ok=True)

# Per-camera analytics engine instances (keyed by camera_id)
_camera_engines: dict[str, AnalyticsEngine] = {}


def get_camera_engine(camera_id: str, model_name: str = "yolo11n", zones: list = None, full_frame_classes: list = None) -> AnalyticsEngine:
    """Get or create an AnalyticsEngine for a specific camera."""
    if camera_id not in _camera_engines:
        _camera_engines[camera_id] = AnalyticsEngine(
            model_name=model_name,
            zones=zones,
            full_frame_classes=full_frame_classes,
        )
    return _camera_engines[camera_id]


def update_camera_engine(camera_id: str, zones: list = None):
    """Update zones on an existing camera engine."""
    if camera_id in _camera_engines and zones is not None:
        _camera_engines[camera_id].set_zones(zones)


# ── Webcam "inline" processor (runs per-frame, called from the WS handler) ──

def process_frame_bytes(jpeg_bytes: bytes, camera_id: str, model_name: str = "yolo11n", zones: list = None) -> dict:
    """
    Decode a JPEG frame, run YOLO tracking with zone-aware counting,
    return a dict ready to be sent as JSON via WebSocket.
    """
    engine = get_camera_engine(camera_id, model_name, zones)

    # Decode JPEG → OpenCV BGR
    arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        return {"event": "error", "message": "Bad frame"}

    result = engine.process_frame(frame)

    return {
        "event": "analytics",
        "resolution": result.resolution,
        "boxes": result.boxes,
        "count": result.total_count,
        "zone_counts": result.zone_counts,
    }


# ── RTSP background thread worker ──────────────────────────────

def _dict_factory(cursor, row):
    return {col[0]: row[i] for i, col in enumerate(cursor.description)}


class IpCameraWorker:
    """
    A background thread that reads from an IP Camera URL, runs YOLO with
    zone-aware counting, burns annotations into the frame, and provides
    a unified MJPEG stream for the frontend, eliminating latency and sync issues.
    """
    def __init__(self, camera_id: str, loop: asyncio.AbstractEventLoop):
        self.camera_id = camera_id
        self.loop = loop
        self.is_running = False
        self._thread = None
        
        # Stream sharing state
        self.latest_frame_bytes: bytes | None = None
        self.frame_lock = threading.Lock()
        self.frame_ready = threading.Event()

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=2)
            
    def get_annotated_frame(self) -> bytes | None:
        """Called by the FastAPI generator to stream the latest annotated JPEG."""
        self.frame_ready.wait(timeout=2.0)
        with self.frame_lock:
            frame_bytes = self.latest_frame_bytes
        self.frame_ready.clear()
        return frame_bytes

    def _broadcast(self, msg: str):
        conns = active_connections.get(self.camera_id, [])
        if not conns:
            return
        async def _send():
            dead = []
            for ws in conns:
                try:
                    await ws.send_text(msg)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                if ws in conns:
                    conns.remove(ws)
        asyncio.run_coroutine_threadsafe(_send(), self.loop)

    def _run(self):
        db_path = settings.database_path
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = _dict_factory
            cam = conn.cursor().execute(
                "SELECT * FROM cameras WHERE id = ?", (self.camera_id,)
            ).fetchone()
            conn.close()
        except Exception as e:
            print(f"[RTSP-{self.camera_id}] DB error: {e}")
            self.is_running = False
            return

        if not cam or not cam.get("url"):
            print(f"[RTSP-{self.camera_id}] No URL configured.")
            self.is_running = False
            return

        # Parse zones and classes from DB
        zones = json.loads(cam.get("zones", "[]")) if isinstance(cam.get("zones"), str) else cam.get("zones", [])
        
        classes_raw = cam.get("classes", "[]")
        full_frame_classes = json.loads(classes_raw) if isinstance(classes_raw, str) else classes_raw

        model_name = cam.get("model_name", "yolo11n")

        engine = get_camera_engine(self.camera_id, model_name, zones, full_frame_classes)

        cap = cv2.VideoCapture(cam["url"])
        if not cap.isOpened():
            print(f"[RTSP-{self.camera_id}] Cannot open stream: {cam['url']}")
            self.is_running = False
            return

        target_fps = 10
        frame_time = 1.0 / target_fps
        last_process_time = 0

        while self.is_running and cap.isOpened():
            # Constantly pull frames from the buffer to ensure we aren't lagging behind and creating glitchy/delayed analytics over the live video
            ret = cap.grab()
            if not ret:
                time.sleep(2)
                cap = cv2.VideoCapture(cam["url"])
                continue

            current_time = time.time()
            if current_time - last_process_time >= frame_time:
                last_process_time = current_time
                ret, frame = cap.retrieve()
                if not ret: continue

                # Match the livestream MJPEG stream downscaling to lock coordinate space
                MAX_WIDTH = 1280
                h, w = frame.shape[:2]
                scale_factor = 1.0
                if w > MAX_WIDTH:
                    scale_factor = MAX_WIDTH / w
                    frame = cv2.resize(frame, (MAX_WIDTH, int(h * scale_factor)), interpolation=cv2.INTER_AREA)

                result = engine.process_frame(frame, scale=scale_factor)
                
                # Burn annotations directly into the video frame
                engine.draw_annotations(frame, result)
                
                # Encode the annotated frame to JPEG for the MJPEG stream
                JPEG_QUALITY = 75
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
                
                with self.frame_lock:
                    self.latest_frame_bytes = buffer.tobytes()
                self.frame_ready.set()

                # Broadcast counts (UI badge updating) but exclude boxes to save massive JSON bandwidth
                payload = json.dumps({
                    "event": "analytics",
                    "count": result.total_count,
                    "zone_counts": result.zone_counts,
                })
                self._broadcast(payload)

        cap.release()


# ── Manager singleton ───────────────────────────────────────────

class CameraWorkerManager:
    def __init__(self):
        self._workers: dict[str, IpCameraWorker] = {}
        self.loop = None

    def initialize(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop

    def spawn_worker(self, camera_id: str):
        if camera_id in self._workers:
            self._workers[camera_id].stop()
        w = IpCameraWorker(camera_id, self.loop)
        self._workers[camera_id] = w
        w.start()

    def kill_worker(self, camera_id: str):
        if camera_id in self._workers:
            self._workers[camera_id].stop()
            del self._workers[camera_id]

    def shutdown_all(self):
        for w in self._workers.values():
            w.stop()
        self._workers.clear()


camera_manager = CameraWorkerManager()
