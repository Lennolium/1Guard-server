#!/usr/bin/env python3

"""
initialization.py: TODO: Headline...

TODO: Description...
"""

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__date__ = "2023-11-25"
__status__ = "Prototype/Development/Production"

# Imports.
import logging

import requests
from urllib.parse import quote

from oneguardai import const

# Child logger.
LOGGER = logging.getLogger(__name__)


def server_reachable(url: str) -> bool:
    try:
        response = requests.head(url=url,
                                 allow_redirects=True,
                                 timeout=const.INIT_TIMEOUT,
                                 )
        if response.status_code != 200:
            LOGGER.warning("Website is NOT reachable. Status code: "
                           f"{response.status_code}."
                           )
            return False
        else:
            return True

    except Exception as e:
        LOGGER.warning(f"Connection with SSL failed. Retrying "
                       f"without SSL now ... {str(e)}"
                       )
        try:
            response2 = requests.head(url=url,
                                      allow_redirects=True,
                                      timeout=const.INIT_TIMEOUT,
                                      verify=False,
                                      )
            if response2.status_code != 200:
                LOGGER.warning("Website is NOT reachable. Status code: "
                               f"{response2.status_code}."
                               )
                return False
            else:
                return True

        except Exception as e:
            LOGGER.warning(f"Website is NOT reachable: {str(e)}.")
            return False


def cloudflare_protected(url: str) -> bool or None:
    """
    Checks if a website is protected by cloudflare, and we thus need to
    use a different approach to scan the website or fetch the data.

    :param url: Pass the url of the website to be checked
    :return: A boolean value
    """

    try:
        response = requests.head(url, timeout=const.CF_TIMEOUT,
                                 allow_redirects=True
                                 )

        if response.status_code != 200:
            LOGGER.error("Could not check if website is cloudflare protected. "
                         f"Response status code: {response.status_code}."
                         f"Response: {response.content}."

                         )
            # Some other kind of access restriction -> bypass needed.
            return True

        headers = response.headers
        server_info = headers.get("Server", "")

        return "cloudflare" in server_info.lower()

    except Exception as e:
        LOGGER.error(
                f"An error occurred while checking if website is cloudflare "
                f"protected: {str(e)}."
                )
        return True


def cloudflare_bypass(url: str) -> requests.Response or None:
    encoded_url = quote(url, safe="")

    # WebScraper Alternatives: ScraperBox, SerpStack, WebScraping.AI
    endpoint = (f"https://api.scrapingant.com/v2/general?url="
                f"{encoded_url}&x-api-key="
                f"{const.API_KEY_SCRAPANT}&proxy_country=DE"
                f"&return_page_source=true")

    try:
        response = requests.get(endpoint, timeout=const.CF_TIMEOUT,
                                allow_redirects=True
                                )

        if response.status_code != 200:
            LOGGER.error("Could not bypass cloudflare protection. Response "
                         f"status code: {response.status_code}."
                         )
            return None

        response_snippet = response.content[250:450]
        if b"suspected phishing site | cloudflare" in response_snippet.lower():
            LOGGER.warning("Cloudflare flagged the website as phishing. "
                           "We can not bypass the protection."
                           )
            return None

        return response

    except Exception as e:
        LOGGER.error(
                f"An error occurred while trying to bypass cloudflare "
                f"protection: {str(e)}. Try another scraper service ..."
                )

        # Try another scraper service.
        second_try = cloudflare_bypass2(url)
        if second_try is not None:
            return second_try

        return None


def cloudflare_bypass2(url: str) -> requests.Response or None:
    payload = {'api_key': const.API_KEY_SCRAPEUP,
               'url': url,
               'render': True,
               }

    try:
        response = requests.get(
                'http://api.scrapeup.com',
                params=payload, allow_redirects=True, timeout=const.CF_TIMEOUT
                )

        if response.status_code != 200:
            LOGGER.error("Could not bypass cloudflare protection. Response "
                         f"status code: {response.status_code}."
                         )
            return None

        response_snippet = response.content[250:450]
        if b"Suspected phishing site | Cloudflare" in response_snippet:
            LOGGER.warning("Cloudflare flagged the website as phishing. "
                           "We can not bypass the protection."
                           )
            return None

        return response

    except Exception as e:
        LOGGER.error(
                f"An error occurred while trying to second cloudflare "
                f"bypass: {str(e)}. Could not scrape ..."
                )
        return None
