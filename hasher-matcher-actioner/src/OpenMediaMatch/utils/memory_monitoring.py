import logging
import os
import time
import tracemalloc
import typing as t
from dataclasses import dataclass
from datetime import datetime

import psutil
from pympler import muppy, summary

logger = logging.getLogger(__name__)

@dataclass
class MemorySnapshot:
    timestamp: float
    process_memory: float  # in MB
    system_memory: float   # in MB
    faiss_memory: t.Optional[float] = None  # in MB
    top_objects: t.Optional[t.List[t.Tuple[str, int]]] = None  # (type_name, size)
    tracemalloc_stats: t.Optional[t.Dict[str, float]] = None  # Memory stats from tracemalloc

class MemoryMonitor:
    def __init__(self, enable_faiss_monitoring: bool = True, enable_detailed_profiling: bool = False):
        self.enable_faiss_monitoring = enable_faiss_monitoring
        self.enable_detailed_profiling = enable_detailed_profiling
        self.snapshots: t.List[MemorySnapshot] = []
        if self.enable_detailed_profiling:
            tracemalloc.start()
        
    def take_snapshot(self) -> MemorySnapshot:
        """Take a snapshot of current memory usage"""
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info().rss / 1024 / 1024  # Convert to MB
        system_memory = psutil.virtual_memory().used / 1024 / 1024  # Convert to MB
        
        # Get FAISS memory if enabled
        faiss_memory = None
        if self.enable_faiss_monitoring:
            try:
                import faiss
                # Try to get memory usage through alternative means
                # This is a fallback since get_mem_usage() is not available
                faiss_memory = process_memory  # Use process memory as approximation
            except ImportError:
                logger.warning("FAISS not available for memory monitoring")
        
        # Get top memory-consuming objects (only if detailed profiling enabled)
        top_objects = None
        tracemalloc_stats = None
        
        if self.enable_detailed_profiling:
            try:
                all_objects = muppy.get_objects()
                summary_objects = summary.summarize(all_objects)
                top_objects = [(str(obj[0]), obj[1]) for obj in summary_objects[:5]]
            except Exception as e:
                logger.warning(f"Failed to get object summary: {e}")
            
            # Get tracemalloc statistics
            try:
                tracemalloc_stats = {}
                snapshot = tracemalloc.take_snapshot()
                for stat in snapshot.statistics('lineno')[:5]:
                    tracemalloc_stats[stat.traceback.format()[0]] = stat.size / 1024 / 1024  # Convert to MB
            except Exception as e:
                logger.warning(f"Failed to get tracemalloc stats: {e}")
        
        snapshot = MemorySnapshot(
            timestamp=time.time(),
            process_memory=process_memory,
            system_memory=system_memory,
            faiss_memory=faiss_memory,
            top_objects=top_objects,
            tracemalloc_stats=tracemalloc_stats
        )
        
        self.snapshots.append(snapshot)
        return snapshot
    
    def log_snapshot(self, message: str = "") -> str:
        """Take a snapshot and log it"""
        snapshot = self.take_snapshot()
        faiss_memory_str = f"{snapshot.faiss_memory:.2f}" if snapshot.faiss_memory is not None else "N/A"
        
        # Format top objects for better readability
        top_objects_str = "\n    ".join([f"{obj[0]}: {obj[1]/1024/1024:.2f} MB" for obj in snapshot.top_objects]) if snapshot.top_objects else "None"
        
        # Format tracemalloc stats for better readability
        tracemalloc_str = "\n    ".join([f"{loc}: {size:.2f} MB" for loc, size in snapshot.tracemalloc_stats.items()]) if snapshot.tracemalloc_stats else "None"
        
        # return as a string

        return f"""
        \n=== Memory Snapshot: {message} ===\n
        Process Memory: {snapshot.process_memory:.2f} MB\n
        System Memory: {snapshot.system_memory:.2f} MB\n
        FAISS Memory: {faiss_memory_str} MB\n
        Top Objects:\n    {top_objects_str}\n
        Top Memory Allocations:\n    {tracemalloc_str}\n
        ============================"""
    
    def get_memory_trend(self) -> t.Dict[str, float]:
        """Calculate memory usage trends"""
        if len(self.snapshots) < 2:
            return {}
        
        first = self.snapshots[0]
        last = self.snapshots[-1]
        
        return {
            "process_memory_change": last.process_memory - first.process_memory,
            "system_memory_change": last.system_memory - first.system_memory,
            "faiss_memory_change": (last.faiss_memory - first.faiss_memory) 
                if last.faiss_memory is not None and first.faiss_memory is not None else None,
            "duration_seconds": last.timestamp - first.timestamp
        }
    
    def log_memory_trend(self) -> str:
        """Log memory usage trends"""
        trend = self.get_memory_trend()
        if not trend:
            return ""
            
        faiss_change_str = f"{trend['faiss_memory_change']:.2f}" if trend['faiss_memory_change'] is not None else "N/A"
        return f"""
        \n=== Memory Usage Trend ===\n
        Process Memory Change: {trend['process_memory_change']:.2f} MB\n
        System Memory Change: {trend['system_memory_change']:.2f} MB\n
        FAISS Memory Change: {faiss_change_str} MB\n
        Duration: {trend['duration_seconds']:.2f} seconds\n
        ============================"""

def monitor_faiss_index_operations(func: t.Callable) -> t.Callable:
    """Decorator to monitor memory usage around FAISS index operations"""
    def wrapper(*args, **kwargs):
        monitor = MemoryMonitor()
        logger.info(monitor.log_snapshot("Before operation"))
        try:
            result = func(*args, **kwargs)
            logger.info(monitor.log_snapshot("After operation"))
            logger.info(monitor.log_memory_trend())
            return result
        except Exception as e:
            logger.info(monitor.log_snapshot("After operation failure"))
            logger.info(monitor.log_memory_trend())
            raise e
    return wrapper 