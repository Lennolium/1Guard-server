#!/usr/bin/env python3

"""
server.py: TODO: Headline...

TODO: Description...
"""

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__build__ = "2023.1"
__date__ = "2023-11-07"
__status__ = "Prototype"

# Imports.
import signal
import sys

import const
from api import api
from utils import log

# Root logger and log counter.
LOG_COUNT = log.LogCount()
LOGGER = log.create_logger(LOG_COUNT)


def exit_handler(signum=None, frame=None, error=False):
    """
    The exit_handler function is a signal handler that catches the
    SIGINT and SIGTERM signals. It then prints out a message to the
    log file, and exits with status 0.

    :param signum: Identify the signal that caused the exit_handle
        to be called
    :param frame: Reference the frame object that called function
    :param error: If True, an error occurred which caused the exit
    :return: None
    """

    # If error is True, an error occurred which caused the exit.
    if error:
        code = 1
        LOGGER.critical(
                "A critical error occurred that caused the server "
                "to exit unexpectedly."
                )

    else:
        code = 0
        LOGGER.info("Exiting the server properly ...")

    sys.exit(code)


def exception_handler(exc_type, exc_value, exc_traceback):
    """
    The exception_handler function is a custom exception handler that
    logs uncaught exceptions to the log file with the level CRITICAL.
    Finally, it calls the exit_handler function to exit the program.

    :param exc_type: Store the exception type
    :param exc_value: Get the exception value
    :param exc_traceback: Get the traceback object
    :return: None
    """

    # Do not log KeyboardInterrupt (Ctrl+C).
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    LOGGER.critical(
            "Uncaught Exception:",
            exc_info=(exc_type, exc_value, exc_traceback),
            )

    exit_handler(error=True)


def main():
    # Register handlers for clean exit of program.
    for sig in [signal.SIGINT, signal.SIGTERM, signal.SIGQUIT]:
        signal.signal(sig, exit_handler)

    # Set the exception hook.
    sys.excepthook = exception_handler

    # Set the log level to debug for development. TODO: remove!
    # 10 = DEBUG, 20 = INFO, 30 = WARNING, 40 = ERROR, 50 = CRITICAL.
    LOGGER.setLevel(10)

    LOGGER.info("--------- Startup: ---------")
    LOGGER.debug(f"APP_PATH: {const.APP_PATH}")
    LOGGER.info("Starting 1Guard server and running startup checks ...")
    LOGGER.info(
            f"You are running 1Guard server version: {__version__} "
            f"({__build__})."
            )

    # Start API flask server.
    api.start()

    # TODO: Implement startup checks here.

    # All startup checks finished without critical errors.
    LOGGER.info("Startup checks done and 1Guard server ready to run!")

    return api.app


if __name__ == "__main__":
    app = main()
