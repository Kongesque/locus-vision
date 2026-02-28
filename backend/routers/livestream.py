import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from services.livestream_manager import livestream_manager

router = APIRouter(
    prefix="/api/livestream",
    tags=["livestream"],
)

@router.get("/{camera_id}/video")
async def video_feed(camera_id: str, request: Request):
    """
    Returns a continuous MJPEG stream.
    """
    stream_ctx = livestream_manager.get_or_create_stream(camera_id)
    # Give the client a generous queue size of 30 frames (about 2 seconds at 15fps)
    # If the network drops, we drop frames instead of backing up RAM.
    client_queue = asyncio.Queue(maxsize=30)
    stream_ctx.video_clients.append(client_queue)
    
    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                # Wait for the next frame from the queue
                frame_bytes = await client_queue.get()
                
                # Format as MJPEG boundary
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        finally:
            stream_ctx.video_clients.remove(client_queue)

    return StreamingResponse(event_generator(), media_type="multipart/x-mixed-replace; boundary=frame")


@router.get("/{camera_id}/events")
async def sse_events(camera_id: str, request: Request):
    """
    Returns a Server-Sent Events (SSE) stream of detection data.
    """
    stream_ctx = livestream_manager.get_or_create_stream(camera_id)
    client_queue = asyncio.Queue(maxsize=100)
    stream_ctx.event_clients.append(client_queue)

    async def sse_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                event_json = await client_queue.get()
                # Server-Sent Events format: 'data: {json}\n\n'
                yield f"data: {event_json}\n\n"
        finally:
            stream_ctx.event_clients.remove(client_queue)

    return StreamingResponse(sse_generator(), media_type="text/event-stream")
