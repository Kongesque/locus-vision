"""
Camera analytics worker.

Two modes:
1. RTSP mode  – A background thread pulls frames via OpenCV and broadcasts YOLO results.
2. Webcam mode – The browser sends JPEG frames over the WebSocket and we process them inline.
"""
import asyncio
import threading
import cv2
import json
import time
import sqlite3
import os
import base64
import numpy as np
from ultralytics import YOLO

from routers.cameras import active_connections
from config import settings

# ── Shared YOLO model cache ─────────────────────────────────────
MODELS_DIR = "data/models"
os.makedirs(MODELS_DIR, exist_ok=True)

_loaded_models = {}

def get_yolo_model(model_name: str):
    if model_name not in _loaded_models:
        print(f"[CameraWorker] Loading model: {model_name}")
        model_path = os.path.join(MODELS_DIR, f"{model_name}.pt")
        try:
            if os.path.exists(model_path):
                _loaded_models[model_name] = YOLO(model_path)
            else:
                print(f"[CameraWorker] Downloading {model_name}...")
                temp = YOLO(f"{model_name}.pt")
                if os.path.exists(f"{model_name}.pt"):
                    os.rename(f"{model_name}.pt", model_path)
                    _loaded_models[model_name] = YOLO(model_path)
                else:
                    _loaded_models[model_name] = temp
        except Exception as e:
            print(f"[CameraWorker] Fallback to yolov8n: {e}")
            _loaded_models[model_name] = YOLO("yolov8n.pt")
    return _loaded_models[model_name]


# ── Webcam "inline" processor (runs per-frame, called from the WS handler) ──

def process_frame_bytes(jpeg_bytes: bytes, model_name: str = "yolo11n") -> dict:
    """
    Decode a JPEG frame, run YOLO tracking, return a dict ready to be sent as JSON.
    """
    model = get_yolo_model(model_name)

    # Decode JPEG → OpenCV BGR
    arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        return {"event": "error", "message": "Bad frame"}

    h, w = frame.shape[:2]

    results = model.track(frame, persist=True, verbose=False)

    boxes_data = []
    if results and results[0].boxes:
        boxes = results[0].boxes.xywh.cpu().numpy()
        class_indices = results[0].boxes.cls.cpu().numpy()
        confs = results[0].boxes.conf.cpu().numpy()
        track_ids = results[0].boxes.id

        if track_ids is not None:
            track_ids = track_ids.int().cpu().tolist()
            for box, tid, cls, conf in zip(boxes, track_ids, class_indices, confs):
                cx, cy, bw, bh = box
                boxes_data.append({
                    "id": int(tid),
                    "x": float(cx - bw / 2),
                    "y": float(cy - bh / 2),
                    "w": float(bw),
                    "h": float(bh),
                    "class": int(cls),
                    "conf": round(float(conf), 2),
                    "label": model.names[int(cls)],
                })

    return {
        "event": "analytics",
        "resolution": {"w": w, "h": h},
        "boxes": boxes_data,
    }


# ── RTSP background thread worker (unchanged concept) ──────────

def _dict_factory(cursor, row):
    return {col[0]: row[i] for i, col in enumerate(cursor.description)}


class RtspWorker:
    """
    A background thread that reads from an RTSP URL, runs YOLO, and pushes
    results into the WebSocket connections registry.
    """
    def __init__(self, camera_id: str, loop: asyncio.AbstractEventLoop):
        self.camera_id = camera_id
        self.loop = loop
        self.is_running = False
        self._thread = None

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=2)

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

        model = get_yolo_model(cam.get("model_name", "yolo11n"))
        cap = cv2.VideoCapture(cam["url"])
        if not cap.isOpened():
            print(f"[RTSP-{self.camera_id}] Cannot open stream: {cam['url']}")
            self.is_running = False
            return

        target_fps = 10
        frame_time = 1.0 / target_fps

        while self.is_running and cap.isOpened():
            t0 = time.time()
            ret, frame = cap.read()
            if not ret:
                time.sleep(2)
                cap = cv2.VideoCapture(cam["url"])
                continue

            if not active_connections.get(self.camera_id):
                time.sleep(0.5)
                continue

            h, w = frame.shape[:2]
            results = model.track(frame, persist=True, verbose=False)

            boxes_data = []
            if results and results[0].boxes:
                boxes = results[0].boxes.xywh.cpu().numpy()
                cls_arr = results[0].boxes.cls.cpu().numpy()
                confs = results[0].boxes.conf.cpu().numpy()
                tids = results[0].boxes.id
                if tids is not None:
                    tids = tids.int().cpu().tolist()
                    for box, tid, cls, conf in zip(boxes, tids, cls_arr, confs):
                        cx, cy, bw, bh = box
                        boxes_data.append({
                            "id": int(tid),
                            "x": float(cx - bw / 2),
                            "y": float(cy - bh / 2),
                            "w": float(bw),
                            "h": float(bh),
                            "class": int(cls),
                            "conf": round(float(conf), 2),
                            "label": model.names[int(cls)],
                        })

            payload = json.dumps({
                "event": "analytics",
                "resolution": {"w": w, "h": h},
                "boxes": boxes_data,
            })
            self._broadcast(payload)

            dt = time.time() - t0
            if dt < frame_time:
                time.sleep(frame_time - dt)

        cap.release()


# ── Manager singleton ───────────────────────────────────────────

class CameraWorkerManager:
    def __init__(self):
        self._workers: dict[str, RtspWorker] = {}
        self.loop = None

    def initialize(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop

    def spawn_rtsp_worker(self, camera_id: str):
        if camera_id in self._workers:
            self._workers[camera_id].stop()
        w = RtspWorker(camera_id, self.loop)
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
