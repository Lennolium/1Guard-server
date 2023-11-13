#!/usr/bin/env python3

"""
scan.py: TODO: Headline...

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
import random

from scan import https


def get_data(domain):
    """
    Get the data for the specified domain.
    -> Call other functions to get the data.
    """

    ssl = https.check_https(domain)
    headers = https.check_security_headers(domain)
    category = https.check_category(domain)

    return {
            "ssl": ssl,
            "headers": headers,
            "category": category,
            }


# TODO: Implement the user score function. Right now it is just a random
#  number (0-15).
def get_user_score_trustpilot(domain):
    return random.randint(0, 15)
