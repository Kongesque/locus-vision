import asyncio
import os
import time
from typing import Dict, Any

from services.onnx_detector import MODELS_DIR

class ModelManager:
    """Manages downloading and exporting YOLO models."""
    def __init__(self):
        self.download_jobs: Dict[str, Dict[str, Any]] = {}

    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """Return the current status of all downloads."""
        return self.download_jobs

    async def start_download(self, base_model: str, precision: str = "fp32"):
        """
        Starts a background download/export job.
        precision: 'fp32', 'fp16', or 'int8'
        """
        job_id = f"{base_model}_{precision}"
        
        if job_id in self.download_jobs and self.download_jobs[job_id]["status"] in ["downloading", "exporting"]:
            return self.download_jobs[job_id]

        self.download_jobs[job_id] = {
            "status": "starting",
            "model": base_model,
            "precision": precision,
            "error": None,
            "started_at": time.time(),
            "updated_at": time.time()
        }

        # Run export in background so we don't block the API
        asyncio.create_task(self._run_export(job_id, base_model, precision))
        
        return self.download_jobs[job_id]

    async def _run_export(self, job_id: str, base_model: str, precision: str):
        try:
            self.download_jobs[job_id]["status"] = "downloading"
            self.download_jobs[job_id]["updated_at"] = time.time()

            # The export script handles both download (.pt) and export (.onnx)
            # Find python executable for the current venv
            import sys
            python_exe = sys.executable
            
            script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "export_model.py")
            
            cmd = [python_exe, script_path, base_model]
            if precision == "fp16":
                cmd.append("--half")
            elif precision == "int8":
                cmd.append("--int8")

            # We assume downloading if it takes a while before exporting
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Monitor output to update state to 'exporting'
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                decoded_line = line.decode('utf-8').strip()
                print(f"[ModelManager] {decoded_line}")
                
                if "Exporting" in decoded_line:
                    self.download_jobs[job_id]["status"] = "exporting"
                    self.download_jobs[job_id]["updated_at"] = time.time()

            await process.wait()
            
            if process.returncode == 0:
                self.download_jobs[job_id]["status"] = "done"
            else:
                stderr = (await process.stderr.read()).decode('utf-8')
                print(f"[ModelManager] Error: {stderr}")
                self.download_jobs[job_id]["status"] = "error"
                self.download_jobs[job_id]["error"] = stderr
                
        except Exception as e:
            print(f"[ModelManager] Exception: {e}")
            self.download_jobs[job_id]["status"] = "error"
            self.download_jobs[job_id]["error"] = str(e)
        finally:
            self.download_jobs[job_id]["updated_at"] = time.time()

model_manager = ModelManager()
