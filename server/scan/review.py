#!/usr/bin/env python3

"""
review.py: TODO: Headline...

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
import json
import logging
import re
import time
from typing import Any, Dict
from urllib.parse import urlparse
import subprocess

import requests
from bs4 import BeautifulSoup
from importlib import import_module
import http.client
from urllib.parse import quote

from oneguardai import const
from oneguardai.scan import initialization
from oneguardai.data import scrape

# Child logger.
LOGGER = logging.getLogger(__name__)


def trustpilot(domain: str) -> dict | dict[float, int]:
    """
    Get the trustpilot reviews for the specified domain.

    We need to scrape the website because TrustPilot does only provide
    a paid API (200 USD per month).
    """

    url = f"https://de.trustpilot.com/review/{domain}"

    try:
        # response = requests.get(url, timeout=const.TIMEOUT)
        response = scrape.get(domain=url)

        if response.success is False:
            LOGGER.error("Could not fetch trustpilot rating. Response status "
                         f"code: {response.response.status_code}."
                         )
            return {}

        if response.response.status_code == 404:
            LOGGER.warning("Could not fetch trustpilot rating: Shop not found."
                           )

            return {}

        elif response.response.status_code != 200:
            LOGGER.error("Could not fetch trustpilot rating. Response status "
                         f"code: {response.response.status_code}."
                         )
            return {}

        rating_element = response.soup.find(
                class_="typography_body-l__KUYFJ "
                       "typography_appearance-subtle__8_H2l"
                )

        rating_count = response.soup.find(
                class_="typography_body-l__KUYFJ "
                       "typography_appearance-default__AAY17"
                )

        # Convert strings to floats.
        if rating_element and rating_count:
            total_rating = rating_element.text.strip()
            total_rating = total_rating.replace(",", ".")
            total_rating = float(total_rating)

            total_count = rating_count.text.strip()
            total_count = total_count.replace("Insgesamt", "").strip()
            total_count = total_count.replace(".", "").strip()
            total_count = int(total_count)

            return {"rating": total_rating, "reviews_count": total_count}

        else:
            return {}

    except Exception as e:
        LOGGER.error("An error occurred while fetching the trustpilot rating:"
                     f" {str(e)}."
                     )
        return {}


def scamadviser(domain: str) -> dict:
    """
    Get the scamadviser score and more data for the specified domain.

    :return: dict with the following keys:
        rating (1-100),
        backlinks (int),
        website_speed (str),
        ssl_certificate_valid (bool)

    """

    url = f"https://www.scamadviser.com/check-website/{domain}"

    try:
        # response = requests.get(url, timeout=const.TIMEOUT)
        response = scrape.get(domain=url)

        if response.success is False:
            raise RuntimeError("Force no ssl.")

        else:
            soup = response.soup

    except Exception as e1:
        LOGGER.warning("Could not fetch scamadviser rating. Trying again with"
                       "out SSL ..."
                       )
        try:
            response = requests.get(url=url,
                                    timeout=const.TIMEOUT,
                                    verify=False,
                                    allow_redirects=True
                                    )

            if response.status_code != 200:
                LOGGER.error("Could not fetch scamadviser rating. Response "
                             f"status code: {response.status_code}."
                             )
                return {}

            soup = BeautifulSoup(response.text, "html.parser")

        except Exception as e2:
            LOGGER.error("Final try to fetch scamadviser rating failed."
                         f"Both errors: {str(e1)}{str(e2)}."
                         )
            return {}

    try:

        # Scamadviser rating score.
        trustscore_div = soup.find("div", {"id": "trustscore"})
        if trustscore_div:
            trustscore_value = int(trustscore_div["data-rating"])
        else:
            trustscore_value = None

        # Backlinks are how many other sites link to specified domain.
        backlinks_div = soup.find("div", {"class": "block__col"},
                                  string="Backlinks"
                                  )
        if backlinks_div:
            backlinks_value = backlinks_div.find_next("div", {
                    "class": "block__col"
                    }
                                                      )
            backlinks_value = int(backlinks_value.string.strip())
        else:
            backlinks_value = None

        # Speed of the website loading.
        website_speed_div = soup.find("div", {"class": "block__col"},
                                      string="Website Speed"
                                      )
        if website_speed_div:
            website_speed_value = website_speed_div.find_next("div", {
                    "class": "block__col"
                    }
                                                              )
            website_speed_value = website_speed_value.string.strip()
        else:
            website_speed_value = None

        # Convert speed values (str) to int.
        if website_speed_value:
            website_speed_value = const.VELOCITY_MAP[website_speed_value]

        # SSL certificate validation.
        ssl_cert_div = soup.find("div", {"class": "block__col"},
                                 string="SSL certificate valid"
                                 )
        if ssl_cert_div:
            ssl_cert_value = ssl_cert_div.find_next("div", {
                    "class": "block__col"
                    }
                                                    )
            if ssl_cert_value.string.strip() == "valid":
                ssl_cert_value = True
            else:
                ssl_cert_value = False

        else:
            ssl_cert_value = None

        results = {"rating": trustscore_value,
                   "backlinks": backlinks_value,
                   "website_speed": website_speed_value,
                   "ssl_certificate_valid": ssl_cert_value,
                   }

        return results

    except Exception as e:
        LOGGER.error("An error occurred while fetching the scamadviser rating:"
                     f" {str(e)}."
                     )
        return {}


def virustotal(domain: str) -> dict:
    """
    Get the virustotal report for the specified domain.
    API-Limit: 500 requests a day, 4 requests a minute.
    """

    url = f"https://www.virustotal.com/api/v3/domains/{domain}"

    headers = {
            "accept": "application/json",
            "x-apikey": const.API_KEY_VT,
            }
    try:
        response = requests.get(url, headers=headers, timeout=const.TIMEOUT)

        if response.status_code != 200:
            LOGGER.error("Could not fetch virustotal rating. Response status "
                         f"code: {response.status_code}."
                         )
            return {}

        response = response.json()

        # Extract popularity and security stats from virustotal
        # api response.
        results = {"popularity": {key: item["rank"] for key, item in
                                  response["data"]["attributes"][
                                      "popularity_ranks"].items()},
                   "security": response["data"]["attributes"][
                       "last_analysis_stats"]
                   }

        return results

    except Exception as e:
        LOGGER.error("An error occurred while fetching the virustotal rating:"
                     f" {str(e)}."
                     )
        return {}


def getsafeonline(domain: str) -> dict[bool] or dict[None]:
    """
    Get the getsafeonline check for the specified domain.
    """

    url = f"https://check.getsafeonline.org/check/{domain}"

    try:
        # response = requests.get(url, timeout=const.TIMEOUT)
        response = scrape.get(domain=url)

        if response.response.status_code != 200:
            LOGGER.error("Could not fetch getsafeonline rating. Response "
                         f"status code: {response.response.status_code}."
                         )
            return {}

        results = {}

        review_sections = response.soup.find_all('div',
                                                 class_='flex flex-col gap-4 '
                                                        'md:flex-row'
                                                 )

        for section in review_sections:
            a_element = section.find("a", class_="text-black")
            source_name = None
            if a_element:
                source_name = a_element.text.strip()[: -1]

            img_element = section.find("img")
            if img_element and source_name is not None:

                alt_text = img_element.get("alt", "").lower()

                if alt_text == "source-positive":
                    results[source_name] = True

                elif alt_text == "source-negative" or alt_text == \
                        "source-neutral":
                    results[source_name] = False

                else:
                    results[source_name] = None

        return results

    except Exception as e:
        LOGGER.error("An error occurred while fetching the getsafeonline "
                     f"checks: {str(e)}."
                     )
        return {}


def pagerank(domain: str) -> dict:
    url = ("https://openpagerank.com/api/v1.0/getPageRank?domains%5B0%5D"
           f"={domain}")

    headers = {"API-OPR": const.API_KEY_PR}

    try:
        response = requests.get(url, headers=headers, timeout=const.TIMEOUT)

        if response.status_code != 200:
            LOGGER.error("Could not fetch PageRank. Response status "
                         f"code: {response.status_code}."
                         )
            return {}

        response = response.json()

        # Check if domain is found in the api response.
        if response["response"][0]["status_code"] != 200:
            LOGGER.error("Could not fetch PageRank. Response: "
                         f"{response['response'][0]['error']}."
                         )
            return {}

        # Extract data from api response.
        results = {"global_rank": int(response["response"][0]["rank"]),
                   "page_rank": int(response["response"][0][
                                        "page_rank_integer"]
                                    ),
                   }

        return results

    except Exception as e:
        LOGGER.error("An error occurred while fetching the PageRank:"
                     f" {str(e)}."
                     )
        return {}


def urlvoid(domain: str) -> dict:
    url = "https://www.urlvoid.com/"
    scan_url = f"https://www.urlvoid.com/scan/{domain}/"

    # POST request.
    payload = {"site": domain, "go": ""}
    headers = {"Referer": scan_url}

    try:
        response = requests.post(url, data=payload, headers=headers)

        if response.status_code != 200:
            LOGGER.error("Could not get URLVoid data. Response status "
                         f"code: {response.status_code}."
                         )
            return {}

        soup = BeautifulSoup(response.text, "html.parser")

        # Get number of detections.
        table = soup.find("table", class_="table-custom")

        detection_counts_cell = table.find("span", class_="font-bold",
                                           string="Detections Counts"
                                           )
        detection_counts = detection_counts_cell.find_next("td").text.strip()
        detection_counts = int(detection_counts.split('/')[0].strip())

        # Check for number of hosted websites at the same ip.
        ip_link_cell = table.find("span", class_="font-bold",
                                  string="IP Address"
                                  )
        ip_link_label = ip_link_cell.find_next("td").text.strip()

        # If no ip address is found, we can not get the number of hosted
        # websites at the same ip.
        if ip_link_label == "Unknown":
            results = {"detections": detection_counts,
                       "sites_hosted_same_ip": "NaN",
                       "sites_hosted_same_ip_detections": "NaN",
                       }

            return results

        ip_link = soup.find("a", string="Find Websites")["href"]

        response2 = requests.get(ip_link, timeout=const.TIMEOUT)

        if response2.status_code != 200:
            LOGGER.error("Could not get URLVoid data. Response status "
                         f"code: {response2.status_code}."
                         )
            return {}

        soup2 = BeautifulSoup(response2.text, "html.parser")

        # Get number of servers hosted at same ip (-1 because we do not
        # count the current domain).
        server_count = len(soup2.select('.table-custom tbody tr'))
        server_count -= 1

        # Check for number of detections of hosted websites at same ip.
        server_detected_count = len(
                soup2.select('.table-custom tbody tr:has(.text-danger)')
                )
        # If there are detections for the current domain, we need to
        # subtract 1, because we do not count detections for the current
        # domain.
        if detection_counts > 0:
            server_detected_count -= 1

        # Extract data from response.
        results = {"detections": detection_counts,
                   "sites_hosted_same_ip": server_count,
                   "sites_hosted_same_ip_detections": server_detected_count,
                   }

        return results

    except Exception as e:
        LOGGER.error("An error occurred while fetching URLVoid data:"
                     f" {str(e)}."
                     )
        return {}


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
                                               timeout=2, profiles="detected",
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
                     f"profiles: {str(e), str(e.output)}."
                     )
        return None


def trustedshops(domain: str) -> dict:
    url = f"https://www.trustedshops.de/shops/?q={domain}"

    try:
        # response = requests.get(url, timeout=const.TIMEOUT)
        response = scrape.get(domain=url)

        if response.response.status_code != 200:
            LOGGER.error(
                    "Could not fetch trustedshops rating. Response status "
                    f"code: {response.response.status_code}."
                    )
            return {}

        first_entry = response.soup.find("a",
                                         class_="ShopResultItemstyles__ResultItem-sc"
                                                "-3gooul-0"
                                         )

        if not first_entry:
            LOGGER.error(
                    "Could not fetch trustedshops rating. Error: Shop not "
                    "found."
                    )
            return {"trusted": False}

        link = first_entry["href"]
        link_split = link.split('/')[4]

        # Not a TrustedShops partner.
        if not link_split.endswith(".html"):
            LOGGER.error(
                    "Could not fetch trustedshops rating. Error: Shop is not "
                    "trustedshop partner."
                    )
            return {"trusted": False}

        response2 = requests.get(link, timeout=const.TIMEOUT)

        if response2.status_code != 200:
            LOGGER.error(
                    "Could not fetch trustedshops rating. Response status "
                    f"code: {response2.status_code}."
                    )
            return {}

        soup2 = BeautifulSoup(response2.text, "html.parser")

        # Get the total rating for that shop.
        total_rating = soup2.find('div', class_='sc-c9c42b4a-4').find('span',
                                                                      class_='sc-c9c42b4a-5'
                                                                      ).get_text(
                strip=True
                )

        rating = float(total_rating.replace(",", "."))

        # Get the total number of reviews submitted for that shop.
        total_reviews = \
            soup2.find('h2', class_='Heading-sc-1w8ymiq-0').find_all(
                    'span', class_='sc-c9c42b4a-11'
                    )[1].get_text(strip=True)

        reviews_count = int(total_reviews.replace(".", "").replace(
                "Bewertungen "
                "insgesamt", ""
                ).strip()
                            )

        return {"trusted": True, "rating": rating,
                "reviews_count": reviews_count
                }

    # Shop is not a TrustedShops partner.
    except Exception as e:
        LOGGER.error(
                f"Could not fetch trustedshops rating. Error: "
                f"{e.__class__.__name__}: {e}."
                )
        return {"trusted": False}


if __name__ == "__main__":
    # BAD EXAMPLE: 11trikots.com

    # PERFORMANCE TESTING (ScamAdviser and GetSafeOnline are slow):
    start = time.perf_counter()
    print(trustpilot("arktis.de"))
    end = time.perf_counter()
    print("TP TIME ELAPSED:", end - start)

    start = time.perf_counter()
    print(trustedshops("arktis.de"))
    end = time.perf_counter()
    print("TS TIME ELAPSED:", end - start)

    start = time.perf_counter()
    print(scamadviser("chicladdy.com"))
    end = time.perf_counter()
    print("SA TIME ELAPSED:", end - start)

    # start = time.perf_counter()
    # print(virustotal("chicladdy.com"))
    # end = time.perf_counter()
    # print("VT TIME ELAPSED:", end - start)

    start = time.perf_counter()
    print(getsafeonline("chicladdy.com"))
    end = time.perf_counter()
    print("GSO TIME ELAPSED:", end - start)

    start = time.perf_counter()
    print(pagerank("chicladdy.com"))
    end = time.perf_counter()
    print("PR TIME ELAPSED:", end - start)

    start = time.perf_counter()
    print(urlvoid("chicladdy.com"))
    end = time.perf_counter()
    print("URLVOID TIME ELAPSED:", end - start)
