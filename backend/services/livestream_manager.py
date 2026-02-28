import asyncio
import cv2
import json
import time
import threading
from typing import AsyncGenerator
from collections import defaultdict
from services.analytics_engine import AnalyticsEngine

class LivestreamManager:
    def __init__(self):
        self.active_streams = {}  # camera_id -> StreamContext
        self.lock = threading.Lock()

    def get_or_create_stream(self, camera_id: str):
        with self.lock:
            if camera_id not in self.active_streams:
                self.active_streams[camera_id] = StreamContext(camera_id)
                self.active_streams[camera_id].start()
            return self.active_streams[camera_id]

class StreamContext:
    def __init__(self, camera_id: str):
        self.camera_id = camera_id
        # We will use asyncio.Queue for broadcasting to connected clients
        # A list of queues, one for each connected client
        self.video_clients = []
        self.event_clients = []
        
        self.engine = AnalyticsEngine(model_name="yolo11n")
        
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        # Run the capture in a background thread to not block the asyncio event loop
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _capture_loop(self):
        # Try to open webcam (0), fallback to a test video if needed
        # For a real VMS this would be an RTSP URL. We'll try 0, then a fallback.
        cap = cv2.VideoCapture(0)
        
        # If webcam fails, grab any sample video we have in cache
        if not cap.isOpened() or not cap.read()[0]:
            print(f"[Livestream] Cannot open webcam 0. Falling back to dummy feed.")
            # For this prototype, we'll just yield a dummy image generating loop if no cam
            self._dummy_loop()
            return

        target_fps = 15
        frame_interval = 1.0 / target_fps

        print(f"[Livestream] Started capture on {self.camera_id}")
        while self._running:
            start_time = time.time()
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # loop if it's a file
                continue

            # Process AI
            result = self.engine.process_frame(frame)
            self.engine.draw_annotations(frame, result)

            # Encode to JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            if ret:
                frame_bytes = buffer.tobytes()
                # Broadcast to all video clients
                for q in self.video_clients:
                    try:
                        q.put_nowait(frame_bytes)
                    except asyncio.QueueFull:
                        pass # drop frame if client is too slow

            # Generate Events based on detections
            if result.boxes:
                # We'll just generate simple events for any bounding box for the prototype
                # Real implementation would do state-diff tracking (e.g. only emit on first entry)
                events = []
                for box in result.boxes:
                    events.append({
                        "type": "person" if box["class"] == 0 else "vehicle" if box["class"] in [2,3,5,7] else "alert",
                        "message": f"{box['label']} detected (Confidence: {box['conf']})",
                        "zone": "Camera View", # fallback zone
                        "timestamp": time.time()
                    })
                
                for ev in events:
                    for q in self.event_clients:
                        try:
                            q.put_nowait(json.dumps(ev))
                        except asyncio.QueueFull:
                            pass

            # Sleep to maintain fps
            elapsed = time.time() - start_time
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        cap.release()

    def _dummy_loop(self):
        """Fallback loop that generates a bouncing color box if no video source is available."""
        import numpy as np
        target_fps = 10
        frame_interval = 1.0 / target_fps
        x, y = 100, 100
        dx, dy = 15, 15
        
        while self._running:
            start_time = time.time()
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            frame[:] = (40, 40, 40) # dark gray
            
            x += dx
            y += dy
            if x <= 0 or x >= 640 - 50: dx *= -1
            if y <= 0 or y >= 480 - 50: dy *= -1
            
            cv2.rectangle(frame, (x, y), (x+50, y+50), (0, 0, 255), -1)
            cv2.putText(frame, "NO CAMERA FEED AVAILABLE", (100, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
            
            ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            if ret:
                frame_bytes = buffer.tobytes()
                for q in self.video_clients:
                    try: q.put_nowait(frame_bytes)
                    except: pass
                    
            # Dummy event
            if x % 30 == 0:
                ev = {"type": "alert", "message": "Dummy motion detected", "zone": "Fallback", "timestamp": time.time()}
                for q in self.event_clients:
                    try: q.put_nowait(json.dumps(ev))
                    except: pass

            elapsed = time.time() - start_time
            if (frame_interval - elapsed) > 0:
                time.sleep(frame_interval - elapsed)


livestream_manager = LivestreamManager()
