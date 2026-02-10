# utils/__init__.py

from .error_extractor import ErrorExtractor
from .time_utils import TimeUtils
from .log_handler import LogHandler

# Compatibility Configurations
def errhandler(e, log, **k): return LogHandler.errhandler(e, log, **k)
def syshandler(m, log, **k): return LogHandler.syshandler(m, log, **k)
def times(): return TimeUtils.timestp()

__all__ = [
    "errhandler",
    "syshandler",
    "times"
]