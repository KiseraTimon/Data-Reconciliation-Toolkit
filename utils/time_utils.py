# utils/time_utils.py

from datetime import datetime

class TimeUtils:
    @staticmethod
    def timestp():
        return datetime.now().strftime("%d-%m-%Y %H:%M:%S")
