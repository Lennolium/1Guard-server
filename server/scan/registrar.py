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
__build__ = "2023.1"
__date__ = "2023-11-07"
__status__ = "Prototype"

# Imports.
import logging
from datetime import datetime, timezone

import country_converter
import pypywhois as whois

# Child logger.
LOGGER = logging.getLogger(__name__)

# Valid TLDs for whois.
VALID_TLDS = whois.validTlds()


def whois_info(domain: str) -> dict:
    # Split domain and tld.
    tld = domain.rsplit(".", 1)[-1]

    if tld not in VALID_TLDS:
        LOGGER.info(f"Unsupported TLD '{tld}' for WHOIS lookup.")
        return {}

    try:
        whois_full = whois.query(domain).__dict__

        # Early exit if WHOIS info is not available.
        if whois_full is None:
            return {}

        # Check how old the domain is.
        try:
            whois_creation = whois_full["creation_date"]
            if isinstance(whois_creation, list):
                creation_date = whois_full["creation_date"][0]
            else:
                creation_date = whois_full["creation_date"]

            created_months = int((datetime.now() - creation_date).days / 30)
        except Exception:
            created_months = 0

        # Check when the domain was last updated.
        try:
            whois_updated = whois_full["last_updated"]
            if isinstance(whois_updated, list):
                updated_date = whois_full["last_updated"][0]
            else:
                updated_date = whois_full["last_updated"]

            updated_months = int(
                    (datetime.now(
                            ) - updated_date).days / 30
                    )
        except Exception:
            updated_months = 0

        # Check when the domain expires.
        try:
            whois_expiration = whois_full["expiration_date"]
            if isinstance(whois_expiration, list):
                expiration_date = whois_full["expiration_date"][0]
            else:
                expiration_date = whois_full["expiration_date"]

            expiration_date = expiration_date.replace(tzinfo=timezone.utc)
            expires_months = int(((expiration_date - datetime.now(
                    timezone.utc
                    )).days
                                  / 30)
                                 )


        except Exception:
            expires_months = 0

        # Check if domain is using DNSSEC.
        try:
            if whois_full["dnssec"] == "unsigned":
                dnssec = False

            elif whois_full["dnssec"] is False:
                dnssec = False

            elif whois_full["dnssec"] is None:
                dnssec = False

            elif whois_full["dnssec"] == True:
                dnssec = True

            elif isinstance(whois_full["dnssec"], list):
                dnssec = whois_full["dnssec"][0]
                if dnssec == "unsigned":
                    dnssec = False
                elif dnssec is False:
                    dnssec = False
            else:
                dnssec = True
        except Exception:
            dnssec = False

        # Get the country of the domain.
        try:
            country = whois_full["country"]

            # Convert country to ISO 3166-1 alpha-2 code if it not already.
            if len(country) != 2:
                country = country_converter.convert(names=country, to='ISO2',
                                                    not_found="NaN"
                                                    )

        except Exception:
            country = "NaN"

        # Check if domain privacy is enabled.
        try:
            privacy_names = ["private", "whoisguard", "privacy", "protected",
                             "redacted", "anonymized", "anonymised", "null",
                             "personal data", "personal information",
                             "applicable laws", "disclosed", "restricted", ]

            if isinstance(whois_full["name"], list):
                whois_name = whois_full["name"][0]
            elif whois_full["name"] is None:
                whois_name = "NaN"
            else:
                whois_name = whois_full["name"]
            try:
                if isinstance(whois_full["org"], list):
                    whois_org = whois_full["org"][0]
                elif whois_full["org"] is None:
                    whois_org = "NaN"
                else:
                    whois_org = whois_full["org"]
            except Exception:
                try:
                    whois_org = whois_full["registrant_organization"]
                    if whois_org is None:
                        whois_org = "NaN"
                except Exception:
                    whois_org = "NaN"

            privacy = False
            for priv in privacy_names:
                if priv in whois_name.lower():
                    privacy = True
                    break

                elif priv in whois_org.lower():
                    privacy = True
                    break
        except Exception:
            privacy = "NaN"

        results = {"created_months": created_months,
                   "last_updated_months": updated_months,
                   "expires_in_months": expires_months,
                   "dnssec": dnssec,
                   "country": country,
                   "domain_privacy": privacy,
                   }

        return results

    except Exception as e:
        LOGGER.info(f"Could not fetch WHOIS info. Error: {str(e)}"
                    )
        return {}


if __name__ == "__main__":
    website_domain = "0000-programasnet.blogspot.com"

    whois_result = whois_info(website_domain)

    if whois_result is not None:
        print("RESULTS:")
        print(whois_result)

    else:
        print("No results ...")
