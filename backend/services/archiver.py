"""
Background Archiver.
Runs periodically (e.g., monthly) to export old raw telemetry to Parquet files and delete it from Active DuckDB.
"""

import time
import threading
from datetime import datetime, timedelta
import logging
from pathlib import Path
from services.duckdb_client import client as db_client

logger = logging.getLogger(__name__)

class Archiver:
    def __init__(self, check_interval_seconds: int = 86400, retention_days: int = 30):
        self.check_interval_seconds = check_interval_seconds  # Check daily
        self.retention_days = retention_days
        self._thread = None
        self._running = False
        self.archive_dir = Path("data/archives")
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Archiver started.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("Archiver stopped.")

    def _run_loop(self):
        while self._running:
            try:
                self.run_archival()
            except Exception as e:
                logger.error(f"Archiver error: {e}")
            
            # Sleep in small chunks to allow quick shutdown
            for _ in range(self.check_interval_seconds):
                if not self._running:
                    break
                time.sleep(1)

    def run_archival(self):
        """
        Export data older than retention_days to Parquet and delete from DB.
        """
        logger.info("Running archival check...")
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
            month_str = cutoff_date.strftime('%Y_%m')
            
            # Archive zone_events
            zone_export_path = self.archive_dir / f"zone_events_{month_str}.parquet"
            db_client.conn.execute(f"""
                COPY (SELECT * FROM zone_events WHERE timestamp < '{cutoff_str}') 
                TO '{zone_export_path}' (FORMAT PARQUET)
            """)
            db_client.conn.execute(f"DELETE FROM zone_events WHERE timestamp < '{cutoff_str}'")
            
            # Archive line_events
            line_export_path = self.archive_dir / f"line_events_{month_str}.parquet"
            db_client.conn.execute(f"""
                COPY (SELECT * FROM line_events WHERE timestamp < '{cutoff_str}') 
                TO '{line_export_path}' (FORMAT PARQUET)
            """)
            db_client.conn.execute(f"DELETE FROM line_events WHERE timestamp < '{cutoff_str}'")
            
            # Archive object_tracks
            track_export_path = self.archive_dir / f"object_tracks_{month_str}.parquet"
            db_client.conn.execute(f"""
                COPY (SELECT * FROM object_tracks WHERE timestamp < '{cutoff_str}') 
                TO '{track_export_path}' (FORMAT PARQUET)
            """)
            db_client.conn.execute(f"DELETE FROM object_tracks WHERE timestamp < '{cutoff_str}'")
            
            logger.info("Archival complete.")
        except Exception as e:
            logger.error(f"Error during archival: {e}")

archiver = Archiver(check_interval_seconds=86400, retention_days=30)  # Check daily, retain 30 days
