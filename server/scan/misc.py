#!/usr/bin/env python3

"""
misc.py: TODO: Headline...

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
import re

import requests
from bs4 import BeautifulSoup

from oneguardai import const

# Child logger.
LOGGER = logging.getLogger(__name__)


def get_favicon(domain: str, soup: BeautifulSoup) -> str or None:
    """
    The get_favicon function takes in a domain and BeautifulSoup object
    as parameters. It then searches the BeautifulSoup object for any
    'link' tags with an attribute of 'rel' that matches either 'shortcut
    icon' or 'icon'. If it finds one, it returns the value of its 'href'
    attribute. If not, it attempts to make a GET request to
    https://{domain}/favicon.ico and return that if successful.

    :param domain: str: Specify the domain of the website
    :param soup: BeautifulSoup: Pass the beautifulsoup object
    :return: The favicon url of the website
    """

    for item in soup.find_all("link", attrs={
            "rel": re.compile("^(shortcut icon|icon)$", re.I)
            }
                              ):
        return item.get("href")

    try:
        testing = requests.get(f"https://{domain}/favicon.ico",
                               timeout=const.TIMEOUT
                               )
        if testing.status_code == 200:
            return f"{domain}/favicon.ico"

    except Exception:
        return None


def favicon_external(domain: str, soup: BeautifulSoup) -> bool or None:
    """
    This function checks if the favicon is loaded from an external
    domain. This is a sign of phishing.

    :param soup: BeautifulSoup: Pass the beautifulsoup object
    :param domain: str: Specify the domain to be checked
    :return: True if the favicon is loaded from an external domain
    """

    favicon = get_favicon(domain, soup)

    # No favicon found.
    if favicon is None:
        LOGGER.info("No favicon was found.")
        return None

    # google --> google.com/favicon.ico
    elif favicon.rfind("/") >= 1 and "http" not in favicon:
        return False

    # https://example.com/favicon.ico
    elif domain in favicon:
        return False

    # popa.com --> https://static.parastorage.com/client/pfavico.ico
    # fb.com --> https://static.xx.fbcdn.net/rsrc.php/yv/r/B8BxsscfVBr.ico
    elif favicon.startswith("http") and domain not in favicon:
        return True

    # 12345.ico --> internal
    else:
        return False


def website_traffic(response: requests.Response) -> int or None:
    """
    The website_traffic function takes in a requests.Response object and
    returns the number of bytes in the response content as an integer or
    None if there is no content.

    :param response: requests.Response: Pass in the response object
    :return: The length/size of the response content in bytes
    """
    try:
        traffic = int(len(response.content))
        return traffic

    except:
        return None


def forwarding(response: requests.Response) -> bool:
    """
    The function takes in a domain name as an argument
    and returns True if the domain is forwarding the user more than
    once. Scammers often use forwarding to hide the original domain
    name.

    :param response: requests.Response: Pass in the response object
    :return: True if the domain is forwarding
    """

    if len(response.history) >= 1:
        return True

    else:
        return False


def impressum_check(soup: BeautifulSoup) -> bool:
    # TODO: implement this function, just a placeholder for now.
    # print(soup)

    try:

        result = soup.find('a', string='Datenschutz')["href"]

    except:
        try:
            result = soup.find('a', string='Privacy')["href"]

        except:
            return False

        return False

    link = f"https://www.11trikots.com{result}"

    request = requests.get(link)
    soup2 = BeautifulSoup(request.text, "html.parser")

    datenschutz_abschnitt = soup2.find('h1', {'id': 'privacyDefaultHeading'})

    if datenschutz_abschnitt:
        datenschutz_text = ""
        next_element = datenschutz_abschnitt.find_next('div')
        while next_element and (
                next_element.name != 'h3' or next_element.name != 'div'):
            datenschutz_text += str(next_element).strip()
            next_element = next_element.find_next_sibling()

    if datenschutz_text is None:
        return False

    else:
        return {"link": link, "text": datenschutz_text}


if __name__ == "__main__":
    request = requests.get(
            "https://plugins.jetbrains.com/plugin/9473-texify-idea/versions"
            )
    soup = BeautifulSoup(request.text, "html.parser")

    result = impressum_check(soup)

    print(result)
