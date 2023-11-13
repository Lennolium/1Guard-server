#!/usr/bin/env python3

"""
log.py: TODO: Headline...

TODO: Description...
"""

# Header.
__author__ = "Lennart Haack"
__email__ = "swiftguard@lennolium.dev"
__license__ = "GNU GPLv3"
__version__ = "0.1.0"
__build__ = "2023.3"
__date__ = "2023-10-09"
__status__ = "Development"

# Imports.
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import const


# Custom logging handler to count warnings, errors and criticals.
class LogCount(logging.Handler):
    def __init__(self):
        super().__init__()
        self.warnings = 0
        self.errors = 0
        self.criticals = 0

    def emit(self, record):
        if record.levelname == "WARNING":
            self.warnings += 1
        elif record.levelname == "ERROR":
            self.errors += 1
        elif record.levelname == "CRITICAL":
            self.criticals += 1


def create_logger(counter):
    # Prepare directory for log file.
    os.makedirs(os.path.dirname(const.LOG_FILE), exist_ok=True)

    # Create root logger.
    logger = logging.getLogger()

    # Log file: Rotate log file every 2 MB and keep 5 old log files.
    file_handler = RotatingFileHandler(
            const.LOG_FILE, backupCount=5, maxBytes=2000000
            )

    # Stdout: Print log messages to stdout (only for testing).
    stdout_handler = logging.StreamHandler(stream=sys.stdout)

    # Define format (level, timestamp, filename, line number, message).
    fmt = logging.Formatter(
            fmt="%(levelname)s | %(asctime)s | %(filename)s:%(lineno)s | %("
                "message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
            )

    # Set the format for the handlers.
    file_handler.setFormatter(fmt)
    stdout_handler.setFormatter(fmt)

    # Add the handlers to the logger (error counter, file and stdout).
    logger.addHandler(counter)
    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)

    # Set the log level to default (INFO).
    logger.setLevel(logging.INFO)

    return logger


def add_handler(logger_obj, dest):
    if dest == "syslog":
        # Syslog/Console: Log to console on Linux.
        syslog_handler = logging.StreamHandler(stream=sys.stderr)

        logger_obj.addHandler(syslog_handler)

    elif dest == "stdout":
        # Stdout: Print log messages to stdout.
        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        # Define format (level, timestamp, filename, line number, message).
        fmt = logging.Formatter(
                fmt="%(levelname)s | %(asctime)s | %(filename)s:%(lineno)s | "
                    "%("
                    "message)s",
                datefmt="%Y-%m-%dT%H:%M:%SZ",
                )
        stdout_handler.setFormatter(fmt)

        logger_obj.addHandler(stdout_handler)

    return logger_obj
