# utils/log_config.py

import logging


request = None
def has_request_context() -> bool:
    return False


logger = logging.getLogger()
logger.setLevel(logging.INFO)


class NewFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = getattr(request, "url", None) if request else None
            record.remote = getattr(request, "remote_addr", None) if request else None
        else:
            record.url = None
            record.remote = None
        return super().format(record)


fileFormat = NewFormatter(
    "**********\nREMOTE: %(remote)s\nSOURCE: %(url)s\nTIME: %(asctime)s\nTYPE: %(levelname)s\nMESSAGE: %(message)s\n",
    datefmt="%Y-%m-%d %H:%M:%S",
)

consoleFormat = NewFormatter(
    "[%(asctime)s] || %(levelname)s || %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
