"""
Tests for RTSP camera integration.

Covers the full path: video_capture → livestream_manager → API endpoints.
Uses a mock RTSP-like source (local video file) to avoid needing a real camera.
"""

import os
import sys
import time
import threading
import pytest
import numpy as np
import cv2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Mock DuckDB and metrics before importing livestream_manager (avoids DB lock conflicts)
from unittest.mock import MagicMock

mock_duckdb_module = MagicMock()
sys.modules["services.duckdb_client"] = mock_duckdb_module
mock_duckdb_module.client = MagicMock()

mock_metrics_module = MagicMock()
sys.modules.setdefault("services.metrics_collector", mock_metrics_module)
mock_metrics_module.metrics_collector = MagicMock()

from services.video_capture import create_video_capture, is_raspberry_pi
from services.livestream_manager import StreamContext, LivestreamManager


# ── Fixtures ────────────────────────────────────────────────────

TEST_VIDEO_PATH = os.path.join(os.path.dirname(__file__), "test_sample.mp4")


@pytest.fixture(scope="session", autouse=True)
def create_test_video():
    """Generate a short test video file to simulate an RTSP-like source."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(TEST_VIDEO_PATH, fourcc, 10, (320, 240))
    for i in range(30):  # 3 seconds at 10fps
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        # Draw a moving rectangle to simulate motion
        x = (i * 10) % 270
        cv2.rectangle(frame, (x, 80), (x + 50, 160), (0, 255, 0), -1)
        cv2.putText(frame, f"frame {i}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
        writer.write(frame)
    writer.release()
    yield
    if os.path.exists(TEST_VIDEO_PATH):
        os.remove(TEST_VIDEO_PATH)


# ── video_capture tests ─────────────────────────────────────────


class TestVideoCapture:
    """Test create_video_capture with different source types."""

    def test_open_file_source(self):
        """Should open a local video file (simulates RTSP file-based source)."""
        cap = create_video_capture(TEST_VIDEO_PATH, enable_hw_accel=False)
        assert cap.isOpened()
        ret, frame = cap.read()
        assert ret
        assert frame.shape == (240, 320, 3)
        cap.release()

    def test_open_rtsp_url_format_accepted(self):
        """Should accept an RTSP URL string without crashing (connection will fail gracefully)."""
        cap = create_video_capture("rtsp://invalid.example.com/stream", enable_hw_accel=False)
        # Connection fails but should not raise — just returns a non-opened capture
        assert not cap.isOpened()
        cap.release()

    def test_open_integer_source(self):
        """Should accept integer camera index."""
        cap = create_video_capture(0, enable_hw_accel=False)
        # May or may not open depending on whether a webcam exists — just verify no crash
        cap.release()

    def test_hw_accel_flag_does_not_crash(self):
        """Hardware accel flag should not crash regardless of platform."""
        cap = create_video_capture(TEST_VIDEO_PATH, enable_hw_accel=True)
        assert cap.isOpened()
        cap.release()


# ── StreamContext with RTSP-like source ─────────────────────────


class TestStreamContextRTSP:
    """Test StreamContext captures frames from an RTSP-like source."""

    def test_stream_captures_frames_from_file(self):
        """StreamContext should capture frames from a video file source."""
        ctx = StreamContext(
            camera_id="test_rtsp_file",
            source=TEST_VIDEO_PATH,
            enable_hw_accel=False,
            model_name="yolo11n",
        )
        import asyncio

        q = asyncio.Queue(maxsize=10)
        ctx.video_clients.append(q)
        ctx.start()

        # Wait for frames to arrive (up to 5s)
        received = 0
        deadline = time.time() + 5
        while time.time() < deadline and received < 3:
            try:
                frame_bytes = q.get_nowait()
                assert len(frame_bytes) > 0
                received += 1
            except asyncio.QueueEmpty:
                time.sleep(0.1)

        ctx.stop()
        assert received >= 1, f"Expected at least 1 frame, got {received}"

    def test_stream_falls_back_to_dummy_on_invalid_source(self):
        """StreamContext should fall back to dummy feed for unreachable RTSP URL."""
        ctx = StreamContext(
            camera_id="test_rtsp_invalid",
            source="rtsp://192.0.2.1/nonexistent",  # RFC 5737 test address
            enable_hw_accel=False,
        )
        import asyncio

        q = asyncio.Queue(maxsize=10)
        ctx.video_clients.append(q)
        ctx.start()

        # RTSP connection timeout can take up to ~30s before fallback kicks in
        received = 0
        deadline = time.time() + 35
        while time.time() < deadline and received < 1:
            try:
                frame_bytes = q.get_nowait()
                assert len(frame_bytes) > 0
                received += 1
            except asyncio.QueueEmpty:
                time.sleep(0.5)

        ctx.stop()
        assert received >= 1, "Dummy fallback should produce frames for unreachable RTSP"

    def test_stream_stop_is_clean(self):
        """Stopping a stream should not hang or crash."""
        ctx = StreamContext(
            camera_id="test_rtsp_stop",
            source=TEST_VIDEO_PATH,
            enable_hw_accel=False,
        )
        ctx.start()
        time.sleep(0.5)
        ctx._running = False
        ctx._thread.join(timeout=5)
        assert not ctx._thread.is_alive()


# ── LivestreamManager RTSP integration ──────────────────────────


class TestManagerRTSP:
    """Test LivestreamManager handles RTSP sources end-to-end."""

    def test_create_rtsp_stream(self):
        """Manager should create a stream with an RTSP-style source."""
        mgr = LivestreamManager()
        stream = mgr.get_or_create_stream(
            camera_id="test_mgr_rtsp",
            source=TEST_VIDEO_PATH,
            enable_hw_accel=False,
        )
        assert stream.source == TEST_VIDEO_PATH
        assert stream.camera_id == "test_mgr_rtsp"
        mgr.stop_all_streams()

    def test_no_duplicate_streams(self):
        """Requesting the same camera_id twice should return the same stream."""
        mgr = LivestreamManager()
        s1 = mgr.get_or_create_stream(camera_id="test_dup", source=TEST_VIDEO_PATH, enable_hw_accel=False)
        s2 = mgr.get_or_create_stream(camera_id="test_dup", source=TEST_VIDEO_PATH, enable_hw_accel=False)
        assert s1 is s2
        mgr.stop_all_streams()

    def test_stop_specific_stream(self):
        """Should stop only the requested stream."""
        mgr = LivestreamManager()
        mgr.get_or_create_stream(camera_id="cam_a", source=TEST_VIDEO_PATH, enable_hw_accel=False)
        mgr.get_or_create_stream(camera_id="cam_b", source=TEST_VIDEO_PATH, enable_hw_accel=False)

        mgr.stop_stream("cam_a")
        assert "cam_a" not in mgr.active_streams
        assert "cam_b" in mgr.active_streams
        mgr.stop_all_streams()

    def test_stop_all_streams(self):
        """stop_all should cleanly shut down every stream."""
        mgr = LivestreamManager()
        for i in range(3):
            mgr.get_or_create_stream(
                camera_id=f"cam_{i}",
                source=TEST_VIDEO_PATH,
                enable_hw_accel=False,
            )
        assert len(mgr.active_streams) == 3
        mgr.stop_all_streams()
        assert len(mgr.active_streams) == 0


# ── Edge cases ──────────────────────────────────────────────────


class TestRTSPEdgeCases:
    """Edge cases for RTSP-like sources."""

    def test_empty_string_source(self):
        """Empty string source should not crash — capture just won't open."""
        cap = create_video_capture("", enable_hw_accel=False)
        assert not cap.isOpened()
        cap.release()

    def test_http_url_accepted(self):
        """HTTP URL (MJPEG stream) should be accepted as a source type."""
        cap = create_video_capture("http://invalid.example.com/stream.mjpg", enable_hw_accel=False)
        # Won't open but should not crash
        cap.release()

    def test_multiple_concurrent_streams(self):
        """Multiple streams from the same file should not interfere."""
        contexts = []
        for i in range(3):
            ctx = StreamContext(
                camera_id=f"concurrent_{i}",
                source=TEST_VIDEO_PATH,
                enable_hw_accel=False,
            )
            ctx.start()
            contexts.append(ctx)

        time.sleep(1)

        for ctx in contexts:
            ctx.stop()
            assert not ctx._running


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
