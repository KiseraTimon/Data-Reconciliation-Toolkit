# utils/error_extractor.py

import traceback

class ErrorExtractor:
    @staticmethod
    def error(e):
        err_type = type(e).__name__
        err_msg = str(e)

        tb_list = traceback.extract_tb(e.__traceback__) if getattr(e, "__traceback__", None) else []

        if tb_list:
            tb = tb_list[-1]
            filename = tb.filename
            line_no = tb.lineno
        else:
            filename = None
            line_no = None

        return (
            f"ERROR TYPE:\n{err_type}\n\n"
            f"ERROR MESSAGE:\n{err_msg if err_msg else None}\n\n"
            f"ERROR ORIGIN:\n{filename}\n\n"
            f"ERROR LINE:\n{line_no}"
        )
