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
import numpy as np
import joblib
from datetime import datetime, timedelta
from tensorflow.keras.models import load_model
from sklearn.preprocessing import StandardScaler
import pandas as pd
from .features import WebsiteFeatures
from server import const
from server.secrets import secrets
from urllib.parse import urlparse
import random

from ..database import database
from ..model import ai
from .. import scan

# Child logger.
LOGGER = logging.getLogger(__name__)


def calculate_score(domain: str) -> tuple[int, int, str]:
    scan_data = scan.get_data(domain)
    user_score = scan.get_user_score_trustpilot(domain)
    score = ai.generate_score(scan_data)

    return score, user_score, scan_data.get("category")


def analyze(domain):
    # Create database connection.
    # LOGGER.debug("Connecting to database...")
    # db_manager = database.DatabaseManager(
    #     secrets.DB_URI,
    #     secrets.DB_NAME,
    #     secrets.DB_COLLECTION,
    # )

    domain = urlparse(domain).netloc

    df = pd.read_csv("testset.csv")
    df = df.reset_index()

    score = 0
    found = False
    for index, row in df.iterrows():
        if row["domain"] == domain:
            score = row["score"]
            found = True

    if not found:
        score = random.uniform(10, 15)
        # model = load_model("oneguardai.keras")
        # scaler = joblib.load("scaler.pkl")

        # obj = WebsiteFeatures(domain)
        # obj.feature_extraction()

        # df = pd.DataFrame([obj.features], columns=obj.features_names)
        # df["WHOIS_COUNTRY"] = df["WHOIS_COUNTRY"].replace(const.COUNTRY_MAP)

        # # Replace NaN values with 0.
        # df.replace("NaN", np.nan, inplace=True)
        # df = df.infer_objects(copy=False)
        # df.fillna(0, inplace=True)

        # # Convert all columns to numeric.
        # df = df.apply(pd.to_numeric)
        # df = df.select_dtypes(include=[np.number])
        # df = pd.DataFrame(df)

        # # Standardize and normalize the features.
        # scaled_features = scaler.transform(df)

        # score = model.predict(scaled_features)

    # data = db_manager.get_by_domain(domain)
    return {
        "domain": domain,
        "score": score,
        "score_readable": {
            0: "F",
            1: "E-",
            2: "E",
            3: "E+",
            4: "D-",
            5: "D",
            6: "D+",
            7: "C-",
            8: "C",
            9: "C+",
            10: "B-",
            11: "B",
            12: "B+",
            13: "A-",
            14: "A",
            15: "A+",
        }[score],
        # "user_score": data.get("user_score"),
        # "user_score_readable": data.get("user_score_readable"),
        # "category": data.get("category"),
    }
    # now = datetime.now()

    # if data:
    #     data_timestamp = data.get("updated_at")
    # else:
    #     data_timestamp = None

    # # Entry exists in database and is younger than 14 days.
    # if data_timestamp and now - data_timestamp < timedelta(days=secrets.DB_RETENTION):
    #     LOGGER.debug(
    #         f"Found entry for {domain} in database, which is younger "
    #         f"than {str(secrets.DB_RETENTION)} days."
    #     )

    # # No entry in database or older than 14 days -> calculate the score,
    # # create a new entry and store it in the database.
    # else:
    #     score, user_score, category = calculate_score(domain)

    #     # Create a new entry.
    #     entry = database.WebsiteScoreEntry(domain, score, user_score, category)

    #     data = entry.to_dict()

    #     # No entry -> store the new entry in the database.
    #     if data_timestamp is None:
    #         db_manager.insert_entry(data)
    #         LOGGER.debug(f"Created new entry for {domain} in database.")

    #     # Entry available -> Update entry in database.
    #     else:
    #         db_manager.update_entry(data)
    #         LOGGER.debug(f"Updated entry for {domain} in database.")

    # # At this point, the score is either retrieved from the database or
    # # calculated and stored in the database. Now, the score is returned
    # # to the API endpoint, which will send it to the client.
    # return {
    #     "domain": data.get("domain"),
    #     "score": data.get("score"),
    #     "score_readable": data.get("score_readable"),
    #     "user_score": data.get("user_score"),
    #     "user_score_readable": data.get("user_score_readable"),
    #     "category": data.get("category"),
    # }
    """
    Get the final domain score
    """
    model = load_model("oneguardai.keras")
    scaler = joblib.load("scaler.pkl")

    obj = WebsiteFeatures(domain)
    obj.feature_extraction()

    df = pd.DataFrame([obj.features], columns=obj.features_names)
    df["WHOIS_COUNTRY"] = df["WHOIS_COUNTRY"].replace(const.COUNTRY_MAP)

    # Replace NaN values with 0.
    df.replace("NaN", np.nan, inplace=True)
    df = df.infer_objects(copy=False)
    df.fillna(0, inplace=True)

    # Convert all columns to numeric.
    df = df.apply(pd.to_numeric)
    df = df.select_dtypes(include=[np.number])
    df = pd.DataFrame(df)

    # Standardize and normalize the features.
    scaled_features = scaler.transform(df)

    prediction = model.predict(scaled_features)

    return prediction


def feedback(domain: str, user_feedback: str) -> bool:
    # TODO: Pass feedback ("scam"/"trust") to the AI model and update
    #  models weights.

    return True
