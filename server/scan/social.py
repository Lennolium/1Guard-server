#!/usr/bin/env python3

"""
social.py: TODO: Headline...

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
import subprocess
from importlib import import_module
from urllib.parse import urlparse

from oneguardai import const

# Child logger.
LOGGER = logging.getLogger(__name__)


def social(domain: str) -> dict or None:
    """
    Get the social media profiles for the specified domain.
    """

    # Search for profiles with url.tld and url (shop.com and shop).
    domain_strip = '.'.join(domain.split('.')[:-1])

    # Need to import social-analyzer dynamically because it has a
    # '-' in its name.
    social_analyzer = import_module("social-analyzer").SocialAnalyzer()

    results = {"all_count": 0, "social_count": 0, "all": [], "social": []}
    for name in [domain, domain_strip]:
        result = social_analyzer.run_as_object(username=name, top=30,
                                               silent=True, output="json",
                                               filter="good", metadata=False,
                                               timeout=const.TIMEOUT,
                                               profiles="detected",
                                               trim=True, method="find",
                                               extract=False, options="link, "
                                                                      "type",
                                               )["detected"]

        for item in result:

            # 'https://my.shop.com/buy/this' -> 'shop'.
            domain_name = urlparse(item["link"]).netloc.split('.')[-2]

            # Save pretty name of social media platform and count.
            if domain_name not in results["all"]:
                results["all_count"] += 1

                results["all"].append(domain_name)

                if "Social" in item["type"]:
                    results["social"].append(domain_name)
                    results["social_count"] += 1

    return results


def social2(domain: str) -> dict or None:
    domain_strip = '.'.join(domain.split('.')[:-1])

    sherlock_local_path = f"{const.APP_PATH}/utils/sherlock/sherlock.py"
    opt_arguments = "--no-color"
    timeout_arg = "--timeout"
    timeout_val = "20"
    output_arg = "--output"
    output_val = ""

    results = {"social_count": 0, "social": []}

    try:
        result = subprocess.run(["python3", sherlock_local_path,
                                 domain_strip, opt_arguments, timeout_arg,
                                 timeout_val, output_arg, output_val],
                                capture_output=True,
                                text=True, check=True, timeout=300
                                )

        # print(result.stdout)

        # Regular expression (only name of social media platform).
        pattern = re.compile(r"\[\+\] (\w+):")

        matches = pattern.findall(result.stdout)

        for match in matches:
            results["social_count"] += 1

            results["social"].append(match)

        return results

    except subprocess.CalledProcessError as e:
        LOGGER.error("An error occurred while fetching the social media "
                     f"profiles: {str(e)} {str(e.output)}."
                     )
        return None
