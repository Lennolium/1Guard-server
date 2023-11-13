#!/usr/bin/env python3

"""
controller.py: TODO: Headline...

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
import logging
from datetime import datetime, timedelta

from database import database
from model import ai
from scan import scan
from secrets import secrets

# Child logger.
LOGGER = logging.getLogger(__name__)


def calculate_score(domain: str) -> tuple[int, int, str]:
    scan_data = scan.get_data(domain)
    user_score = scan.get_user_score_trustpilot(domain)
    score = ai.generate_score(scan_data)

    return score, user_score, scan_data.get("category")


def analyze(domain):
    # Create database connection.
    LOGGER.debug("Connecting to database...")
    db_manager = database.DatabaseManager(secrets.DB_URI, secrets.DB_NAME,
                                          secrets.DB_COLLECTION,
                                          )

    data = db_manager.get_by_domain(domain)
    now = datetime.now()

    if data:
        data_timestamp = data.get("updated_at")
    else:
        data_timestamp = None

    # Entry exists in database and is younger than 14 days.
    if data_timestamp and now - data_timestamp < timedelta(
            days=secrets.DB_RETENTION
            ):

        LOGGER.debug(f"Found entry for {domain} in database, which is younger "
                     f"than {str(secrets.DB_RETENTION)} days."
                     )

    # No entry in database or older than 14 days -> calculate the score,
    # create a new entry and store it in the database.
    else:
        score, user_score, category = calculate_score(domain)

        # Create a new entry.
        entry = database.WebsiteScoreEntry(domain, score, user_score,
                                           category
                                           )

        data = entry.to_dict()

        # No entry -> store the new entry in the database.
        if data_timestamp is None:
            db_manager.insert_entry(data)
            LOGGER.debug(f"Created new entry for {domain} in database.")

        # Entry available -> Update entry in database.
        else:
            db_manager.update_entry(data)
            LOGGER.debug(f"Updated entry for {domain} in database.")

    # At this point, the score is either retrieved from the database or
    # calculated and stored in the database. Now, the score is returned
    # to the API endpoint, which will send it to the client.
    return {"domain": data.get("domain"),
            "score": data.get("score"),
            "score_readable": data.get("score_readable"),
            "user_score": data.get("user_score"),
            "user_score_readable": data.get("user_score_readable"),
            "category": data.get("category")
            }


def feedback(domain: str, user_feedback: str) -> bool:
    # TODO: Pass feedback ("scam"/"trust") to the AI model and update
    #  models weights.

    return True
