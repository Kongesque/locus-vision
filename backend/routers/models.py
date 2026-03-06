import os
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

from services.model_manager import model_manager
from services.onnx_detector import list_models
from services.onnx_detector import MODELS_DIR

router = APIRouter(prefix="/api/models", tags=["Models"])

class DownloadRequest(BaseModel):
    model_name: str  # e.g., 'yolo11s'
    precision: str   # 'fp32', 'fp16', 'int8'

@router.get("/registry")
async def get_model_registry():
    """Get the list of all available models on disk."""
    return list_models()

@router.post("/download")
async def trigger_download(req: DownloadRequest):
    """Trigger an async download/export for a model size and precision."""
    job = await model_manager.start_download(req.model_name, req.precision)
    return job

@router.get("/download/status")
async def get_download_status() -> Dict[str, Dict[str, Any]]:
    """Poll the status of active and recent model downloads."""
    return model_manager.get_status()
