import os
import glob
import logging
from fastapi import APIRouter, Request, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Any

from services.model_manager import model_manager, get_installed_models, resolve_model, load_model_catalog
from services.onnx_detector import list_models, MODELS_DIR
from database import get_app_setting

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".onnx"}
MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500 MB

router = APIRouter(prefix="/api/models", tags=["Models"])


class DownloadRequest(BaseModel):
    model_name: str        # e.g., 'yolo11s'
    precision: str | None = None  # Optional — auto-resolved from hardware if omitted


@router.get("/registry")
async def get_model_registry(request: Request):
    """
    Get the enriched model registry.

    Returns detected backends and all catalog models with installation status
    and auto-resolved active format. If the catalog hasn't been loaded yet
    (e.g. during tests), falls back to the legacy flat file list.
    """
    catalog = getattr(request.app.state, "model_catalog", None)
    backends = getattr(request.app.state, "backends", None)

    # Fallback: catalog not loaded — return legacy format
    if catalog is None or backends is None:
        return {"backends": [], "models": [], "default_model": "yolo11n", "legacy": list_models()}

    models = get_installed_models(catalog, backends)
    default_model = await get_app_setting("default_model", "yolo11n")
    return {"backends": backends, "models": models, "default_model": default_model}


@router.get("/registry/legacy")
async def get_model_registry_legacy():
    """Legacy endpoint: flat list of .onnx filenames on disk."""
    return list_models()


@router.post("/download")
async def trigger_download(req: DownloadRequest, request: Request):
    """
    Trigger an async download/export for a model.

    If precision is omitted, auto-selects the best precision based on
    detected hardware backends (prefers int8 > fp16 > fp32).
    """
    precision = req.precision
    if precision is None:
        # Auto-resolve: pick best precision from detected backends
        backends = getattr(request.app.state, "backends", [])
        if "onnx_int8" in backends:
            precision = "int8"
        elif "onnx_fp16" in backends:
            precision = "fp16"
        else:
            precision = "fp32"

    job = await model_manager.start_download(req.model_name, precision)
    return job


@router.get("/download/status")
async def get_download_status() -> dict[str, dict[str, Any]]:
    """Poll the status of active and recent model downloads."""
    return model_manager.get_status()


@router.post("/upload")
async def upload_model(file: UploadFile = File(...)):
    """
    Upload a custom ONNX model file.

    Validates the file extension and ONNX header, then saves to data/models/.
    The model becomes immediately available for selection.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Accepted: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Sanitize filename: keep only alphanumeric, hyphens, underscores
    base_name = os.path.splitext(os.path.basename(file.filename))[0]
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in base_name)
    if not safe_name:
        raise HTTPException(status_code=400, detail="Invalid filename")

    target_filename = f"{safe_name}{ext}"
    target_path = os.path.join(MODELS_DIR, target_filename)
    tmp_path = target_path + ".tmp"

    os.makedirs(MODELS_DIR, exist_ok=True)

    try:
        # Stream to temp file with size check
        total_size = 0
        with open(tmp_path, "wb") as f:
            while True:
                chunk = await file.read(65536)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_UPLOAD_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE // (1024 * 1024)} MB"
                    )
                f.write(chunk)

        # Validate with onnxruntime: load and check structure
        import onnxruntime as ort
        try:
            session = ort.InferenceSession(tmp_path, providers=["CPUExecutionProvider"])
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid ONNX file — could not load model: {e}"
            )

        try:
            input_meta = session.get_inputs()[0]
            output_meta = session.get_outputs()[0]
            in_shape = input_meta.shape   # expect [1, 3, H, W]
            out_shape = output_meta.shape  # expect [1, 4+num_classes, N]

            warnings = []

            # Validate input shape: [batch, 3, H, W]
            if len(in_shape) != 4:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported input shape {in_shape}. Expected [1, 3, H, W] for YOLO models."
                )
            if isinstance(in_shape[1], int) and in_shape[1] != 3:
                raise HTTPException(
                    status_code=400,
                    detail=f"Expected 3 input channels, got {in_shape[1]}. This doesn't appear to be an RGB image model."
                )

            # Validate output shape: [1, 4+num_classes, N]
            if len(out_shape) == 3:
                # Determine which dim is the "attributes" dim (4 + num_classes)
                # YOLO outputs [1, 84, N] where 84 < N typically, or [1, N, 84]
                dim1 = out_shape[1] if isinstance(out_shape[1], int) else None
                dim2 = out_shape[2] if isinstance(out_shape[2], int) else None

                num_classes = None
                if dim1 is not None and dim1 >= 5:
                    num_classes = dim1 - 4  # attrs dim is [1]
                if dim2 is not None and dim2 >= 5 and (num_classes is None or dim2 < dim1):
                    num_classes = dim2 - 4  # attrs dim is [2]

                if num_classes is not None and num_classes != 80:
                    warnings.append(
                        f"Model has {num_classes} classes (COCO has 80). "
                        f"Detection will work but class labels may not match."
                    )
            else:
                warnings.append(
                    f"Unexpected output shape {out_shape}. "
                    f"Expected [1, 4+num_classes, N] for YOLO detection models."
                )

            logger.info(
                "Validated ONNX model: input=%s %s, output=%s %s",
                input_meta.name, in_shape,
                output_meta.name, out_shape,
            )
        finally:
            del session

        # Atomic rename
        os.replace(tmp_path, target_path)
        size_mb = round(total_size / (1024 * 1024), 1)
        logger.info("Uploaded model: %s (%.1f MB)", target_filename, size_mb)

        result = {
            "filename": target_filename,
            "model_name": safe_name,
            "size_mb": size_mb,
            "input_shape": [s if isinstance(s, int) else None for s in in_shape],
            "output_shape": [s if isinstance(s, int) else None for s in out_shape],
        }
        if warnings:
            result["warnings"] = warnings
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Upload failed: %s", e)
        raise HTTPException(status_code=500, detail="Upload failed")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.delete("/{model_name}")
async def delete_model(model_name: str, request: Request):
    """
    Remove all format files for a model from data/models/.

    Looks up the model in the catalog to find its known filenames,
    then deletes any that exist on disk. Also removes any files
    matching the model name pattern as a fallback.
    """
    catalog = getattr(request.app.state, "model_catalog", None)
    deleted_files: list[str] = []

    # Strategy 1: Delete known catalog files
    if catalog:
        model_entry = catalog.get("models", {}).get(model_name, {})
        for fmt_info in model_entry.get("formats", {}).values():
            file_path = os.path.join(MODELS_DIR, fmt_info["file"])
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_files.append(fmt_info["file"])

    # Strategy 2: Fallback — delete any files matching the model name pattern
    # Catches legacy files like yolo11n_int8.onnx, yolo11n_half.onnx, yolo11n.onnx
    for pattern in [f"{model_name}.onnx", f"{model_name}_*.onnx", f"{model_name}*.hef"]:
        for path in glob.glob(os.path.join(MODELS_DIR, pattern)):
            basename = os.path.basename(path)
            if basename not in deleted_files:
                os.remove(path)
                deleted_files.append(basename)

    if not deleted_files:
        raise HTTPException(status_code=404, detail=f"No files found for model '{model_name}'")

    return {"deleted": deleted_files, "model_name": model_name}
