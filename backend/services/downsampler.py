"""
Background Downsampler.
Runs periodically to aggregate raw tracking stats into hourly materialized views or downsampled tables.
"""

import time
import threading
from datetime import datetime
import logging
from services.duckdb_client import client as db_client

logger = logging.getLogger(__name__)

class Downsampler:
    def __init__(self, interval_seconds: int = 3600):
        self.interval_seconds = interval_seconds
        self._thread = None
        self._running = False

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Downsampler started.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("Downsampler stopped.")

    def _run_loop(self):
        while self._running:
            try:
                self.run_aggregation()
            except Exception as e:
                logger.error(f"Downsampler aggregation error: {e}")
            
            # Sleep in small chunks to allow quick shutdown
            for _ in range(self.interval_seconds):
                if not self._running:
                    break
                time.sleep(1)

    def run_aggregation(self):
        """
        Create/update materialized views or aggregated tables.
        For example, creating hourly zone counts.
        """
        logger.info("Running downsampling aggregation...")
        try:
            # We can use DuckDB to create an aggregated table from raw data
            # For phase 1, we just demonstrate creating an hourly aggregation table
            db_client.conn.execute("""
                CREATE TABLE IF NOT EXISTS hourly_zone_stats AS
                SELECT 
                    date_trunc('hour', timestamp) as hour,
                    camera_id,
                    zone_id,
                    COUNT(DISTINCT track_id) as unique_visitors,
                    AVG(dwell_time) as avg_dwell_time
                FROM zone_events
                WHERE event_type = 'enter'
                GROUP BY 1, 2, 3
            """)
            
            # In a real continuous aggregation, we might do an INSERT/UPSERT here
            # For simplicity, we just rebuild it or append new hours
            # e.g., using a high-water mark.
            
            # E.g.
            # db_client.conn.execute("""
            #     INSERT INTO hourly_zone_stats
            #     SELECT ... FROM zone_events WHERE timestamp > (SELECT MAX(hour) FROM hourly_zone_stats)
            # """)
            
            logger.info("Downsampling aggregation complete.")
        except Exception as e:
            logger.error(f"Error during aggregation: {e}")

downsampler = Downsampler(interval_seconds=3600)  # run hourly
