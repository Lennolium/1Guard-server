#!/usr/bin/env python3

"""
features.py: TODO: Headline...

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
import time

import requests
from bs4 import BeautifulSoup


from ..scan import domain_url, https_ssl, misc, registrar, review, script
from ..utils import log
import scrape

# Root logger and log counter.
if __name__ == "__main__":
    # Root logger and log counter.
    LOG_COUNT = log.LogCount()
    LOGGER = log.create(LOG_COUNT)
else:
    # Child logger.
    LOGGER = logging.getLogger(__name__)


class WebsiteFeatures:
    features_names = [
        # Domain specific features.
        "DOMAIN_LENGTH",
        "SUBDOMAIN",
        "PORT",
        "AT_SYMBOL",
        "PRE_SUFFIX",
        "HTTPS_HOSTNAME",
        "IP_ADDRESS",
        "SHORTENING",
        "REDIRECTING",
        "SUSPICIOUS_TLD",
        # Security and HTML-Header features.
        "HTTPS",
        "HTTPS_WILDCARD",
        "HSTS",
        "CSP",
        "X_CONTENT_TYPE_OPTIONS",
        "X_FRAME_OPTIONS",
        "SECURE_COOKIES",
        # Script features.
        "MOUSE_OVER",
        "RIGHT_CLICK",
        "POPUP",
        "I_FRAME",
        # General Website/HTML-Body features (misc).
        "FAVICON",
        "WEBSITE_TRAFFIC",
        "FORWARDING",
        # Review sites features: TrustPilot.
        "TP_RATING",
        "TP_REVIEWS_COUNT",
        # Review sites features: ScamAdviser.
        "SA_RATING",
        "SA_BACKLINKS",
        "SA_WEBSITE_SPEED",
        "SA_SSL_CERT",
        # Review sites features: VirusTotal.
        # "VT_RANK_STATVOO", "VT_RANK_ALEXA", "VT_RANK_CISCO",
        # "VT_SEC_HARMLESS", "VT_SEC_MALICIOUS", "VT_SEC_SUSPICIOUS",
        # Review sites features: GetSafeOnline.
        "GSO_MALTIVERSE",
        "GSO_APWG",
        "GSO_COMPLYTRON",
        "GSO_DNSFILTER",
        "GSO_FLASHSTART",
        "GSO_IQGLOBAL",
        "GSO_PULSEDIVE",
        "GSO_QUAD9",
        # Review sites features: PageRank.
        "PR_GLOBAL_RANK",
        "PR_PAGE_RANK",
        # Review sites features: URLVoid.
        "UV_DETECTIONS",
        "UV_SITES_SAME_IP",
        "UV_SITES_SAME_IP_DETECTIONS",
        # Review sites features: TrustedShops.
        "TS_TRUSTED",
        "TS_RATING",
        "TS_REVIEWS_COUNT",
        # WHOIS features.
        "WHOIS_CREATED_MONTHS",
        "WHOIS_LAST_UPDATED_MONTHS",
        "WHOIS_EXPIRES_IN_MONTHS",
        "WHOIS_DNSSEC",
        "WHOIS_COUNTRY",
        "WHOIS_PRIVACY",
        # Social media features (Only number of accounts yet).
        # "ALL_ACCOUNTS", "SOCIAL_ACCOUNTS", "SOCIAL_ACCOUNTS2"
    ]

    def __init__(self, domain: str):

        self.domain = domain
        self.url = f"https://{domain}"
        self.alive = None

        self.response = None
        self.soup = None

        # Feature values and names.
        self.features = []
        self.features_count = len(self.features_names)
        self.features_count_nan = len(self.features_names)

        # Start the initialization process.
        self.initialization()

        # Stop here if website is not reachable during initialization.
        if self.alive is False:
            return

    def initialization(self):

        LOGGER.info("------------------ START -------------------")
        LOGGER.info(f"Domain: {self.domain}")

        response = scrape.get(domain=self.domain)

        if response:
            if response.success:
                self.alive = True
                self.response = response.response
                self.soup = response.soup

    def feature_extraction(self):

        if self.alive:
            LOGGER.info("Website is reachable. Starting feature extraction " "...")
        else:
            LOGGER.info("----------------- SKIPPING -----------------")
            return

        start_time = time.perf_counter()

        # Domain specific features -> domain.py
        self.features.append(domain_url.length_domain(self.domain))
        self.features.append(domain_url.subdomain(self.domain))
        self.features.append(domain_url.port(self.domain))
        self.features.append(domain_url.at_symbol(self.domain))
        self.features.append(domain_url.pre_suffix(self.domain))
        self.features.append(domain_url.https_hostname(self.domain))
        self.features.append(domain_url.ip_addr(self.domain))
        self.features.append(domain_url.shortening_service(self.domain))
        self.features.append(domain_url.redirecting(self.domain))
        self.features.append(domain_url.suspicious_tld(self.domain))

        # Security and HTML-Header features -> https.py
        if encr := https_ssl.https_encrypted(self.domain):
            self.features.append(True)  # HTTPS enabled (good)
            self.features.append(encr.get("wildcard", True))
        else:
            self.features.append(False)  # HTTPS disabled (bad)
            self.features.append(True)  # HTTPS wildcard enabled (bad)

        sec_headers = https_ssl.security_headers(self.response)
        self.features.append(sec_headers.get("strict-transport-security", "NaN"))
        self.features.append(sec_headers.get("content-security-policy", "NaN"))
        self.features.append(sec_headers.get("x-content-type-options", "NaN"))
        self.features.append(sec_headers.get("x-frame-options", "NaN"))
        self.features.append(sec_headers.get("secure-cookies", "NaN"))

        # Script features -> script.py
        self.features.append(script.statusbar_mouseover(self.response))
        self.features.append(script.rightclick_disabled(self.response))
        self.features.append(script.popup_window(self.response))
        self.features.append(script.i_frame(self.response))

        # General Website/HTML-Body features -> misc.py
        self.features.append(misc.favicon_external(self.domain, self.soup))
        self.features.append(misc.website_traffic(self.response))
        self.features.append(misc.forwarding(self.response))

        # TrustPilot -> review.py
        tp_results = review.trustpilot(self.domain)
        self.features.append(tp_results.get("rating", "NaN"))
        self.features.append(tp_results.get("reviews_count", "NaN"))

        # ScamAdviser -> review.py
        sa_results = review.scamadviser(self.domain)
        self.features.append(sa_results.get("rating", "NaN"))
        self.features.append(sa_results.get("backlinks", "NaN"))
        self.features.append(sa_results.get("website_speed", "NaN"))
        self.features.append(sa_results.get("ssl_certificate_valid", "NaN"))

        # VirusTotal -> review.py REMOVED DUE TO API LIMITS.
        # vt_results = review.virustotal(self.domain)
        # self.features.append(vt_results.get("popularity", "NaN").get(
        # "Statvoo",
        #                                                              "NaN"
        #                                                              )
        #                      )
        # self.features.append(vt_results.get("popularity", "NaN").get("Alexa",
        #                                                              "NaN"
        #                                                              )
        #                      )
        # self.features.append(
        #         vt_results.get("popularity", "NaN").get("Cisco Umbrella",
        #                                                 "NaN"
        #                                                 )
        #         )
        #
        # self.features.append(vt_results.get("security", "NaN").get(
        # "harmless",
        #                                                            "NaN"
        #                                                            )
        #                      )
        # self.features.append(vt_results.get("security", "NaN").get(
        # "malicious",
        #                                                            "NaN"
        #                                                            )
        #                      )
        # self.features.append(
        #         vt_results.get("security", "NaN").get("suspicious",
        #                                               "NaN"
        #                                               )
        #         )

        # GetSafeOnline -> review.py
        gso_results = review.getsafeonline(self.domain)
        self.features.append(gso_results.get("Maltiverse", "NaN"))
        self.features.append(gso_results.get("APWG", "NaN"))
        self.features.append(gso_results.get("Complytron", "NaN"))
        self.features.append(gso_results.get("DNSFilter", "NaN"))
        self.features.append(gso_results.get("FlashStart", "NaN"))
        self.features.append(gso_results.get("IQ Global", "NaN"))
        self.features.append(gso_results.get("Pulsedive", "NaN"))
        self.features.append(gso_results.get("Quad9", "NaN"))

        # PageRank -> review.py
        pr_results = review.pagerank(self.domain)
        self.features.append(pr_results.get("global_rank", "NaN"))
        self.features.append(pr_results.get("page_rank", "NaN"))

        # URLVoid -> review.py
        uv_results = review.urlvoid(self.domain)
        self.features.append(uv_results.get("detections", "NaN"))
        self.features.append(uv_results.get("sites_hosted_same_ip", "NaN"))
        self.features.append(uv_results.get("sites_hosted_same_ip_detections", "NaN"))

        # TrustedShops -> review.py
        ts_results = review.trustedshops(self.domain)
        self.features.append(ts_results.get("trusted", "NaN"))
        self.features.append(ts_results.get("rating", "NaN"))
        self.features.append(ts_results.get("reviews_count", "NaN"))

        # WHOIS -> registrar.py
        whois_results = registrar.whois_info(self.domain)
        self.features.append(whois_results.get("created_months", "NaN"))
        self.features.append(whois_results.get("last_updated_months", "NaN"))
        self.features.append(whois_results.get("expires_in_months", "NaN"))
        self.features.append(whois_results.get("dnssec", "NaN"))
        self.features.append(whois_results.get("country", "NaN"))
        self.features.append(whois_results.get("domain_privacy", "NaN"))

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time

        for index, feature in enumerate(self.features):
            if feature == "NaN":
                self.features_count -= 1

            # Replace None or empty string with "NaN".
            if feature is None or feature == "":

                # Save modified feature back into list.
                self.features_count -= 1
                self.features[index] = "NaN"

            # Convert bool to int (True = 1, False = 0).
            elif feature in [True, False]:

                # Save modified feature back into list.
                self.features[index] = feature * 1

        LOGGER.info(f"Features (without NaN): {self.features_count}/" f"{self.features_count_nan}")
        LOGGER.info(f"Total Time elapsed: {elapsed_time:.2f} s")
        LOGGER.info("------------------- END --------------------")


if __name__ == "__main__":
    # obj = WebsiteFeatures("11trikots.com")

    obj = WebsiteFeatures("arktis.de")

    obj.feature_extraction()

    print("NAMES:", obj.features_names)
    print("FEATURES:", obj.features)

    exit()

    # Convert to pandas dataframe. just for testing.
    # import pandas as pd
    #
    # df = pd.DataFrame([obj.features], columns=obj.features_names)
    # # save dataframe to csv
    # df.to_csv("test.csv", index=False)
    #
    # # TODO: features: emoji/unicodes, homographen
