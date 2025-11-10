import gc
import logging
import os
import platform
from typing import Optional

try:
    import psutil  # type: ignore[import-untyped]

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


def get_memory_info(label: str = "", logger: Optional[logging.Logger] = None) -> dict:
    """
    Get comprehensive memory information for the current process.

    Returns a dictionary with memory statistics including RSS, VMS,
    available system memory, and memory percentage.
    """
    info = {
        "label": label,
        "psutil_available": PSUTIL_AVAILABLE,
    }

    if not PSUTIL_AVAILABLE:
        if logger:
            logger.warning("psutil not available - limited memory info")
        return info

    try:
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        virtual_mem = psutil.virtual_memory()

        info.update(
            {
                "process_rss_mb": mem_info.rss / (1024 * 1024),
                "process_vms_mb": mem_info.vms / (1024 * 1024),
                "system_total_mb": virtual_mem.total / (1024 * 1024),
                "system_available_mb": virtual_mem.available / (1024 * 1024),
                "system_used_mb": virtual_mem.used / (1024 * 1024),
                "system_percent": virtual_mem.percent,
                "process_percent": process.memory_percent(),
            }
        )

        # Add platform-specific info if available
        if hasattr(mem_info, "shared"):
            info["process_shared_mb"] = mem_info.shared / (1024 * 1024)

    except Exception as e:
        if logger:
            logger.warning("Failed to get memory info: %s", str(e))
        info["error"] = str(e)

    return info


def log_memory_info(label: str = "", logger: Optional[logging.Logger] = None) -> None:
    """
    Log detailed memory information for monitoring and debugging.

    Useful for tracking memory usage at specific points in the application,
    especially during index building, swapping, or request handling.
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    info = get_memory_info(label, logger)

    if not info.get("psutil_available"):
        logger.info("[%s] Memory info: psutil not available", label)
        return

    if "error" in info:
        logger.warning("[%s] Memory info error: %s", label, info["error"])
        return

    logger.info(
        "[%s] Memory: Process RSS=%.1fMB VMS=%.1fMB (%.1f%% of system) | "
        "System: Used=%.1fMB Available=%.1fMB Total=%.1fMB (%.1f%% used)",
        label,
        info.get("process_rss_mb", 0),
        info.get("process_vms_mb", 0),
        info.get("process_percent", 0),
        info.get("system_used_mb", 0),
        info.get("system_available_mb", 0),
        info.get("system_total_mb", 0),
        info.get("system_percent", 0),
    )


def trim_process_memory(
    logger: Optional[logging.Logger] = None, label: str = ""
) -> bool:
    """
    Aggressively attempt to return freed memory to the OS.

    - Always runs gc.collect() first
    - On Linux/glibc systems, calls malloc_trim(0) if available
    - Logs memory info before and after

    Returns True if malloc_trim was successfully invoked; False otherwise.
    """
    # Log memory before trimming
    if logger:
        log_memory_info(f"{label} (before trim)", logger)

    # Always collect Python garbage first
    collected = gc.collect()
    if logger:
        logger.debug("%s Collected %d objects via gc.collect()", label, collected)

    # Only Linux/glibc generally supports malloc_trim
    system = platform.system().lower()
    if system != "linux":
        if logger:
            logger.debug(
                "%s trim_process_memory: malloc_trim not supported on %s", label, system
            )
        return False

    try:
        import ctypes  # noqa: WPS433

        libc = ctypes.CDLL("libc.so.6")
        if hasattr(libc, "malloc_trim"):
            libc.malloc_trim(0)
            if logger:
                logger.info("%s Called malloc_trim(0) to release freed memory", label)
                # Log memory after trimming
                log_memory_info(f"{label} (after trim)", logger)
            return True
        if logger:
            logger.debug("%s trim_process_memory: libc has no malloc_trim", label)
    except OSError as exc:  # pragma: no cover — platform specific (lib load)
        if logger:
            logger.debug(
                "%s trim_process_memory: failed to load libc: %s", label, str(exc)
            )
        return False
    except AttributeError as exc:  # pragma: no cover — platform specific (symbol)
        if logger:
            logger.debug(
                "%s trim_process_memory: malloc_trim symbol not available: %s",
                label,
                str(exc),
            )
        return False
    return False
