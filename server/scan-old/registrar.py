#!/usr/bin/env python3

"""
registrar.py: TODO: Headline...

TODO: Description...
"""

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__date__ = "2023-11-11"
__status__ = "Prototype/Development/Production"

# Imports.
import logging

import whois

# Child logger.
LOGGER = logging.getLogger(__name__)


def get_whois_info(domain):
    try:
        domain_info = whois.whois(domain)
        return domain_info
    except Exception as e:
        LOGGER.error(f"Error fetching whois data: {str(e)}")
        return None


if __name__ == "__main__":
    website_domain = "google.com"
    whois_info = get_whois_info(website_domain)

    if whois_info:
        print(whois_info)
    else:
        print("WHOIS-Informationen nicht verfügbar.")
