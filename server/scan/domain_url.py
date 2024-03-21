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
import ipaddress
import logging

import re
import time

from oneguardai import const

# Child logger.
LOGGER = logging.getLogger(__name__)


def length_domain(domain: str) -> int:
    """
    The function takes in a domain and returns its character length.

    :param domain: Pass in the domain name of an url
    :return: A int value
    """

    domain_no_tld = domain.rsplit(".", 1)[0]

    return len(domain_no_tld)


def subdomain(domain: str) -> bool:
    """
    The function uses regular expressions to count the number of dots in
    the input string and returns True if the domain is a subdomain.
    sub.domain.com --> True
    sub.sub.domain.com --> True
    domain.com --> False

    :param domain: Pass in the domain name that is being checked
    :return: True if there are more than 2 dots in the domain name
    """

    dots = len(re.findall(r"\.", domain))

    if dots >= 2:
        return True

    else:
        return False


def port(domain: str) -> bool:
    """
    The port function takes a domain as input and returns True if the port
    is not standard (443) or insecure (80).
    If no port is specified, it will return False.

    :param domain: str: Specify the domain to be checked
    :return: True if the domain is insecure and false otherwise
    """

    # No port specified -> secure.
    if ":" not in domain:
        return False

    port_domain = domain.split(":")

    # Standard https port -> secure.
    if port_domain[1] == "443":
        return False

    # No standard port or insecure http port (80) -> insecure.
    else:
        return True


def at_symbol(domain: str) -> bool:
    """
    The function checks if the domain contains an @ symbol.
    https://www.amazon.com:infoupdate@69.10.142.34 --> seems to be an
    amazon link, but the browser ignores the part before the @ symbol,
    thus opens the ip address in the browser: 69.10.142.34.


    :param domain: Domain to check
    :return: True if the domain contains an @ symbol
    """

    if "@" in domain:
        return True

    else:
        return False


def percent_symbol(domain: str) -> bool:
    """
    The function checks if the domain contains an % symbol.



    :param domain: Domain to check
    :return: True if the domain contains an % symbol
    """

    if "%" in domain:
        return True

    else:
        return False


def pre_suffix(domain: str) -> bool:
    """
    The function checks if the domain has a prefix or suffix.
    https://www.paypal-cgi.us/webscr.php?cmd=LogIn --> seems to be a
    PayPal link, but paypal-cgi.us is a phishing website.

    :param domain: Check if the domain contains a hyphen
    :return: A boolean value
    """

    if "-" in domain:
        return True

    else:
        return False


def https_hostname(domain: str) -> bool:
    """
    The function checks if the domain has a fake https prefix (e.g.
    http://https-www-paypal-com.com/ --> phishing website).

    :param domain: Check if the domain contains a fake https prefix
    :return: True if the domain contains a fake https prefix
    """

    if "https" in domain or "HTTPS" in domain:
        return True

    else:
        return False


def ip_addr(domain: str) -> bool:
    """
    The  function takes a domain name as input and returns 1 if
    the domain is an IP address, 0 otherwise.

    :param domain: Check if the domain is a valid ip address
    :return: 1 if the domain is an ip address and 0 otherwise
    """

    try:
        ipaddress.ip_address(domain)
        return True
    except:
        return False


def shortening_service(domain: str) -> bool:
    """
    The shortening_service function takes a domain as an argument and
    returns True if the domain is a shortening service. It uses the
    SHORTENING_RE regular expression to determine whether it is a
    shortening service.

    :param domain: Check if the domain is a shortening service
    :return: True if the domain is a shortening service, and
        False otherwise
    """

    match = const.SHORTENING_RE.search(domain)
    if match:
        return True

    else:
        return False


def redirecting(domain: str) -> bool:
    """
    The redirecting function takes in a domain as an argument and
    returns True if the domain is redirecting to another website.
    https://usa.visa.com/track/dyredir.jsp?rDirl=http://200.251.251.11
    --> seems to be a visa link, but due to a vulnerability (XSS) in the
    usa.visa.com site, the user is redirected to a malicious website.

    :param domain: Check if the domain contains '//', which is a sign of
        redirection to another website
    :return: True if the domain is redirecting to another page
    """

    if domain.rfind("//") > 0:
        return True

    else:
        return False


def suspicious_tld(domain: str) -> bool:
    """
    The suspicious_tld function takes in a domain as an argument and
    returns True if the domain has a suspicious top-level domain (TLD).
    https://www.amazon.eg --> seems to be an amazon link, but .eg is the
    country code top-level domain (ccTLD) for Egypt.

    :param domain: Check if the domain has a suspicious top-level domain
    :return: True if the domain has a suspicious top-level domain
    """

    tld = domain.rsplit(".")[-1]

    if tld in const.SUSPICIOUS_TLD:
        return True

    else:
        return False
