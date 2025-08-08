import gc
import logging
import platform
from typing import Optional


def trim_process_memory(logger: Optional[logging.Logger] = None, label: str = "") -> bool:
    """
    Aggressively attempt to return freed memory to the OS.

    - Always runs gc.collect() first
    - On Linux/glibc systems, calls malloc_trim(0) if available

    Returns True if malloc_trim was successfully invoked; False otherwise.
    """
    # Always collect Python garbage first
    gc.collect()

    # Only Linux/glibc generally supports malloc_trim
    system = platform.system().lower()
    if system != "linux":
        if logger:
            logger.debug("%s trim_process_memory: malloc_trim not supported on %s", label, system)
        return False

    try:
        import ctypes  # noqa: WPS433

        libc = ctypes.CDLL("libc.so.6")
        if hasattr(libc, "malloc_trim"):
            libc.malloc_trim(0)
            if logger:
                logger.info("%s Called malloc_trim(0) to release freed memory", label)
            return True
        if logger:
            logger.debug("%s trim_process_memory: libc has no malloc_trim", label)
    except Exception as exc:  # pragma: no cover — platform specific
        if logger:
            logger.debug("%s trim_process_memory: malloc_trim not available: %s", label, str(exc))
    return False


