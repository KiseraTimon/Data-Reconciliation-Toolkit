# utils/log_handler.py

import os
import logging
from logging import FileHandler

from .log_config import logger, fileFormat, consoleFormat
from .time_utils import TimeUtils
from .error_extractor import ErrorExtractor


class LogHandler:
    """
    Method to process error logs
    """
    @staticmethod
    def errhandler(e=None, log=None, path=None):
        if path:
            os.makedirs(f"logs/errors/{path}", exist_ok=True)
            logFile = f"{path}/{log}"
        else:
            os.makedirs("logs/errors", exist_ok=True)
            logFile = log

        file_path = f"logs/errors/{logFile}.log"

        header = f"CRITICAL ERROR @ {TimeUtils.timestp()}. CHECK *{logFile.upper()}*\n\n"
        details = ErrorExtractor.error(e)

        console = logging.StreamHandler()
        console.setFormatter(consoleFormat)
        logger.addHandler(console)
        try:
            logger.error(header)
        finally:
            logger.removeHandler(console)

        file_handler = FileHandler(file_path, mode="a")
        file_handler.setFormatter(fileFormat)
        logger.addHandler(file_handler)
        try:
            logger.error(f"\n---\n{details}\n---\n")
        finally:
            logger.removeHandler(file_handler)


    """
    Method to process system info logs
    """
    @staticmethod
    def syshandler(msg=None, log=None, path=None):
        if path:
            os.makedirs(f"logs/system/{path}", exist_ok=True)
            logFile = f"{path}/{log}"
        else:
            os.makedirs("logs/system", exist_ok=True)
            logFile = log

        file_path = f"logs/system/{logFile}.log"

        header = f"SYSTEM INFORMATION @ {TimeUtils.timestp()}. CHECK *{logFile.upper()}*\n\n"

        console = logging.StreamHandler()
        console.setFormatter(consoleFormat)
        logger.addHandler(console)
        try:
            logger.info(header)
        finally:
            logger.removeHandler(console)

        file_handler = FileHandler(file_path, mode="a")
        file_handler.setFormatter(fileFormat)
        logger.addHandler(file_handler)
        try:
            logger.info(f"\n---\n{msg}\n---\n")
        finally:
            logger.removeHandler(file_handler)

