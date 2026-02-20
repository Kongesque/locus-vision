import json
import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import List, Dict

from database import get_db
from models import Camera, CameraCreate

router = APIRouter(
    prefix="/api/cameras",
    tags=["cameras"],
    responses={404: {"description": "Not found"}},
)

# In-memory registry of active WebSocket connections for camera analytics
# Format: { "camera_id": [WebSocket, ...] }
active_connections: Dict[str, List[WebSocket]] = {}

@router.post("/", response_model=Camera)
async def create_camera(camera: CameraCreate):
    """
    Register a new camera (RTSP or Webcam) and optionally its initial zones/model.
    """
    db = await get_db()
    try:
        # Check if ID already exists
        cursor = await db.execute("SELECT id FROM cameras WHERE id = ?", (camera.id,))
        if await cursor.fetchone():
            raise HTTPException(status_code=400, detail="Camera ID already exists")

        zones_json = json.dumps(camera.zones) if camera.zones is not None else "[]"
        classes_json = json.dumps(camera.classes) if camera.classes is not None else "[]"

        await db.execute(
            """
            INSERT INTO cameras (id, name, type, url, device_id, status, zones, model_name, classes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                camera.id,
                camera.name,
                camera.type,
                camera.url,
                camera.device_id,
                "idle",
                zones_json,
                camera.model_name or "yolo11n",
                classes_json
            )
        )
        await db.commit()

        # Fetch it back
        cursor = await db.execute("SELECT * FROM cameras WHERE id = ?", (camera.id,))
        row = await cursor.fetchone()
        
        row_dict = dict(row)
        row_dict["zones"] = json.loads(row_dict["zones"]) if row_dict["zones"] else []
        row_dict["classes"] = json.loads(row_dict["classes"]) if row_dict["classes"] else []
        
        return Camera(**row_dict)
    finally:
        await db.close()


@router.put("/{camera_id}")
async def update_camera(camera_id: str, camera: CameraCreate):
    """
    Update an existing camera's zones, model, or stream configuration.
    Usually called right before switching to the Livestream page.
    """
    db = await get_db()
    try:
        cursor = await db.execute("SELECT id FROM cameras WHERE id = ?", (camera_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Camera not found")

        zones_json = json.dumps(camera.zones) if camera.zones is not None else "[]"
        classes_json = json.dumps(camera.classes) if camera.classes is not None else "[]"

        await db.execute(
            """
            UPDATE cameras 
            SET name = ?, type = ?, url = ?, device_id = ?, zones = ?, model_name = ?, classes = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (
                camera.name,
                camera.type,
                camera.url,
                camera.device_id,
                zones_json,
                camera.model_name or "yolo11n",
                classes_json,
                camera_id
            )
        )
        await db.commit()

        return JSONResponse({"status": "success", "message": "Camera updated"})
    finally:
        await db.close()


@router.get("/{camera_id}", response_model=Camera)
async def get_camera(camera_id: str):
    """
    Get a specific camera by ID.
    """
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM cameras WHERE id = ?", (camera_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Camera not found")

        row_dict = dict(row)
        row_dict["zones"] = json.loads(row_dict["zones"]) if row_dict["zones"] else []
        row_dict["classes"] = json.loads(row_dict["classes"]) if row_dict["classes"] else []
        return Camera(**row_dict)
    finally:
        await db.close()


@router.get("/", response_model=List[Camera])
async def list_cameras():
    """
    List all configured cameras.
    """
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM cameras ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        
        cameras = []
        for row in rows:
            row_dict = dict(row)
            row_dict["zones"] = json.loads(row_dict["zones"]) if row_dict["zones"] else []
            row_dict["classes"] = json.loads(row_dict["classes"]) if row_dict["classes"] else []
            cameras.append(Camera(**row_dict))
            
        return cameras
    finally:
        await db.close()


@router.websocket("/{camera_id}/ws")
async def websocket_endpoint(websocket: WebSocket, camera_id: str):
    """
    WebSocket endpoint for streaming real-time YOLO analytics metadata to the frontend.
    """
    await websocket.accept()
    
    if camera_id not in active_connections:
        active_connections[camera_id] = []
    
    active_connections[camera_id].append(websocket)
    
    try:
        # TODO: A separate Python background worker should be pulling RTSP frames,
        # running YOLO, and pushing messages into a queue. For now, we accept messages
        # from the client or ping them to keep the connection alive.
        while True:
            # We just wait for messages from the browser or standard health pings
            data = await websocket.receive_text()
            
            # If the backend worker had a result, it would broadcast here:
            # await websocket.send_json({"boxes": [...], "zones": [...]})
    except WebSocketDisconnect:
        active_connections[camera_id].remove(websocket)
        if not active_connections[camera_id]:
            del active_connections[camera_id]

