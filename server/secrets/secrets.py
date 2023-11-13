#!/usr/bin/env python3

"""
secrets.py: TODO: Headline...

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
import os

# Database credentials. We get the sensitive data from environment vars.
DB_NAME = "1guard_db"
DB_COLLECTION = "website_scores"
DB_URI = os.environ["MONGODB_URI"]
DB_RETENTION = 14

# API.
API_SECRET_KEY = "PasswordToIssueTokens"  # TODO: Change to env var.
API_ACCESS_KEY = "SuperSafePasswordToAccessTheAPI"  # TODO: Change to env var.
API_THROTTLE = 5  # Number of requests per second allowed per user.
