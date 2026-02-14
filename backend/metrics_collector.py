# Historical metrics tracking for Media Basher
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict
import psutil
import logging

logger = logging.getLogger(__name__)

class MetricsCollector:
    def __init__(self):
        self.metrics_history: List[Dict] = []
        self.max_history = 1000  # Keep last 1000 data points
        self.collection_interval = 60  # Collect every 60 seconds
        self.is_running = False

    async def start_collection(self):
        """Start collecting metrics in the background"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting metrics collection")
        
        while self.is_running:
            try:
                await self.collect_metrics()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(self.collection_interval)

    async def collect_metrics(self):
        """Collect current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metric = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cpu_percent": cpu_percent,
                "ram_percent": ram.percent,
                "ram_used": ram.used,
                "ram_total": ram.total,
                "disk_percent": disk.percent,
                "disk_used": disk.used,
                "disk_total": disk.total
            }
            
            self.metrics_history.append(metric)
            
            # Keep only recent metrics
            if len(self.metrics_history) > self.max_history:
                self.metrics_history = self.metrics_history[-self.max_history:]
                
        except Exception as e:
            logger.error(f"Error in collect_metrics: {e}")

    def stop_collection(self):
        """Stop collecting metrics"""
        self.is_running = False
        logger.info("Stopped metrics collection")

    def get_metrics(self, hours: int = 1) -> List[Dict]:
        """Get metrics for the last N hours"""
        if not self.metrics_history:
            return []
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        filtered = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m['timestamp']) > cutoff_time
        ]
        
        return filtered

    def get_aggregated_metrics(self, hours: int = 24) -> Dict:
        """Get aggregated statistics for the last N hours"""
        metrics = self.get_metrics(hours)
        
        if not metrics:
            return {
                "cpu_avg": 0,
                "cpu_max": 0,
                "ram_avg": 0,
                "ram_max": 0,
                "disk_avg": 0,
                "data_points": 0
            }
        
        cpu_values = [m['cpu_percent'] for m in metrics]
        ram_values = [m['ram_percent'] for m in metrics]
        disk_values = [m['disk_percent'] for m in metrics]
        
        return {
            "cpu_avg": sum(cpu_values) / len(cpu_values),
            "cpu_max": max(cpu_values),
            "ram_avg": sum(ram_values) / len(ram_values),
            "ram_max": max(ram_values),
            "disk_avg": sum(disk_values) / len(disk_values),
            "data_points": len(metrics),
            "time_range_hours": hours
        }

metrics_collector = MetricsCollector()