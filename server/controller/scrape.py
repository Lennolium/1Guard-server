#!/usr/bin/env python3

"""
scrape.py: TODO!

TODO: Description...
"""

# Header.
__author__ = "Lennart Haack"
__email__ = "simple-header@lennolium.dev"
__license__ = "GNU GPLv3"
__version__ = "0.1.0"
__date__ = "2024-02-07"
__status__ = "Development"
__github__ = "https://github.com/Lennolium/simple-header"

# Imports.
import os.path
import pathlib
import json
import logging
import re
import random

import httpx
import cloudscraper
import waybackpy

import simple_header
from bs4 import BeautifulSoup
from urllib.parse import quote

from oneguardai.utils import log
from oneguardai import const
from oneguardai.data import exceptions

# Root logger and log counter.
if __name__ == "__main__":
    # Root logger and log counter.
    LOG_COUNT = log.LogCount()
    LOGGER = log.create(LOG_COUNT)
else:
    # Child logger.
    LOGGER = logging.getLogger(__name__)


class WebScraperContext:
    """
    This class serves as the context for the WebScraper object. It is
    used to store settings, input, properties, and results of the
    scraping process across different methods and classes.

    :ivar int timeout_connect: Timeout for the initial connection to the
        website.
    :ivar int timeout_tools: Timeout for the internal scraping tools.
    :ivar int timeout_services: Timeout for external scraping services.
    :ivar str domain: The domain of the website to be scraped.
    :ivar bool force_services: If True, only use external services.
    :ivar str url: The URL of the website to be scraped.
    :ivar str url_encoded: The URL of the website to be scraped, encoded
        for use in a URL.
    :ivar dict headers: The headers used for the request to the website.
    :ivar bool success: True if the scraping process was successful,
        otherwise False.
    :ivar httpx.Response response: The response object of the website.
    :ivar BeautifulSoup soup: The BeautifulSoup object of the website.
    """

    # Overall class settings.
    timeout_connect = None
    timeout_tools = None
    timeout_services = None

    def __init__(self) -> None:
        # Input.
        self.domain = None
        self.force_services = None

        # Properties.
        self.url = None
        self.url_encoded = None
        self.headers = None
        self.success = None

        # Results.
        self.response = None
        self.soup = None

    def __str__(self) -> str:
        """
        Return a string representation of the object.

        :return: A string representation of the object.
        :rtype: str
        """

        return (f"WebScraperContext("
                f"domain={self.domain!r}, "
                f"force_services={self.force_services!r}, "
                f"url={self.url!r}, "
                f"url_encoded={self.url_encoded!r}, "
                f"headers={self.headers!r}, "
                f"success={self.success!r}, "
                f"response={self.response!r}, "
                f"soup={self.soup!r})"
                )


class ConnectionManager:
    """
    This class manages the first connection to the website and provides
    methods to figure out the best way to connect to the website (SSL,
    headers, ...). It also provides methods to generate headers for the
    request utilizing our self-written simple-header library.

    :ivar WebScraperContext ctx: The context object for shared settings
        and properties.
    """

    def __init__(self, ctx: WebScraperContext) -> None:
        """
        Initialize the ConnectionManager object by passing the context
        object for shared settings and properties.

        :param ctx: Pass the context for shared instance attributes.
        :type ctx: WebScraperContext
        """
        self.ctx = ctx

    @staticmethod
    def generate_headers(url: str) -> list[dict[str, str]]:
        """
        Generate a list of headers for the request.

        :param url: Pass the url of the website to be scraped.
        :type url: str
        :return: A list of headers.
        :rtype: list[dict[str, str]]
        """

        # Getting the 10 most common user agents and their corresponding
        # plausible, fake browser headers.
        headers = []
        for i, ua in enumerate(simple_header.sua.get(num=10,
                                                     mobile=False,
                                                     force_cached=True
                                                     )
                               ):
            headers.append(
                    simple_header.get_dict(
                            url=url,
                            user_agent=ua,
                            seed=None if i < 7 else i
                            )
                    )
        return headers

    def connect(
            self,
            domain: str,
            ) -> httpx.Response:
        """
        First connect normally to the website and fetch the data.

        :param domain: Pass the domain of the website to be scraped.
        :type domain: str
        :return: A response object if successful, otherwise exception.
        :rtype: httpx.Response | NotReachableError.
        :raises: NotReachableError.
        """

        if domain.startswith(("http://", "https://")):
            domain = domain.split("://", maxsplit=1)[1]

        for protocol in ("https://", "http://"):
            ssl_verify = True if protocol == "https://" else False
            url = f"{protocol}{domain}"

            # Take the most plausible and common header. Otherwise,
            # shuffle the headers and take a random one.
            headers = random.SystemRandom().choice(
                    self.generate_headers(url=url)
                    )

            try:
                with httpx.Client(verify=ssl_verify) as client:
                    response = client.get(
                            url=url,
                            headers=headers,
                            timeout=self.ctx.timeout_connect,
                            follow_redirects=True,
                            )

                # Failed status code: Try next without SSL.
                if response.status_code != 200:
                    LOGGER.info(
                            f"Trying to connect to '{protocol}{domain}' "
                            f"... Failed!"
                            )
                    continue

                # Success: Set instance attributes and return response.
                LOGGER.info(
                        f"Trying to connect to '{protocol}{domain}' ... "
                        f"Success!"
                        )
                self.ctx.url = url
                self.ctx.url_encoded = quote(url, safe="")
                self.ctx.headers = headers

                return response

            except (httpx.HTTPError, ConnectionError):
                LOGGER.info(
                        f"Trying to connect to '{protocol}{domain}' ... "
                        f"Failed!"
                        )
                if ssl_verify:
                    LOGGER.info(f"Retrying without SSL now.")
                continue

        else:
            raise exceptions.NotReachableError(domain)


class ResponseHandler:
    """
    This class handles the response object of the website and provides
    methods to check and process the response.

    :ivar WebScraperContext ctx: The context object for shared settings
        and properties.
    """

    def __init__(self, ctx: WebScraperContext) -> None:
        """
        Initialize the ResponseHandler object by passing the context
        object for shared settings and properties.

        :param ctx: Pass the context for shared instance attributes.
        :type ctx: WebScraperContext
        """
        self.ctx = ctx

    @staticmethod
    def cloudflare_flagged(response: httpx.Response) -> None:
        """
        Checks if a website is flagged as phishing by Cloudflare, and
        thus we can not access it.

        :return: None if website is not flagged, otherwise exception.
        :rtype: None | CloudflareFlaggedError.
        :raises: CloudflareFlaggedError.
        """

        try:
            response_snippet = response.content[250:450]

            if (b"suspected phishing site | cloudflare" in
                    response_snippet.lower()):
                LOGGER.debug(
                        f"The website is flagged as phishing by CloudFlare."
                        )
                raise exceptions.CloudflareFlaggedError(response.url)

        except AttributeError:
            response_snippet = response.text[250:450]

            if ("suspected phishing site | cloudflare" in
                    response_snippet.lower()):
                LOGGER.debug(
                        f"The website is flagged as phishing by CloudFlare."
                        )
                raise exceptions.CloudflareFlaggedError(response.url)

    @staticmethod
    def cloudflare_check(response: httpx.Response) -> bool:
        """
        Checks if a website is protected by CloudFlare Captcha, and we
        thus need to use different approaches to bypass the protection
        to scrape the website.

        :param response: Pass the response object of the website.
        :type response: httpx.Response.
        :return: True if the website is cloudflare protected.
        :rtype: bool.
        """

        heads = response.headers
        server_info = heads.get("Server", "")
        result = "cloudflare" in server_info.lower()

        if result:
            LOGGER.debug(f"The website is protected by a CloudFlare "
                         f"captcha and other anti-bot measures."
                         )

        return result

    @staticmethod
    def soupify(response: httpx.Response) -> BeautifulSoup:
        """
        Create a BeautifulSoup object from the response object.

        :param response: Pass the response object of the website.
        :type response: httpx.Response
        :return: A BeautifulSoup object
        :rtype: BeautifulSoup
        """

        try:
            return BeautifulSoup(response.text, "html.parser")

        except Exception as e:
            raise exceptions.BeautifulSoupError(
                    f"{e.__class__.__name__}: {e}"
                    )

    def cloudflare_bypass(self):
        # force_services -> only scrapingant, scrapeup, dripcrawler
        # 1. Cloudscraper
        # 2. Free Scraping API
        # 3. ScrapingAnt API
        # 4. ScrapeUp API
        # 5. Selenium
        # 6. Scrapy-Splash
        # 7. Google Cache
        # 8. Public Proxy
        # TODO: vllt free scraping nach den anderen services, weil
        #  sehr langsam und vllt nicht so zuverlässig... dann lieber
        #  erst api credits verbrauchen und dann auf free zurückfallen.

        pass


class ToolManager:
    """
    This class manages the internal scraping tools, libraries, and
    APIs. All tools are used to bypass cloudflare protection and fetch
    the website's data successfully.

    :ivar WebScraperContext ctx: The context object for shared settings
        and properties.
    """

    def __init__(self, ctx: WebScraperContext) -> None:
        """
        Initialize the ToolManager object by passing the context
        object for shared settings and properties.

        :param ctx: Pass the context for shared instance attributes.
        :type ctx: WebScraperContext
        """
        self.ctx = ctx

    def tool_cloudscraper(self) -> httpx.Response:
        """
        Use the cloudscraper library to bypass cloudflare protection.

        :return: A response object if successful, otherwise exception.
        :rtype: httpx.Response | CloudScraperError.
        :raises: CloudScraperError.
        """

        try:
            if self.ctx.url.startswith("http://"):
                ssl = False
            else:
                ssl = True
            scraper = cloudscraper.create_scraper()
            response = scraper.get(
                    url=self.ctx.url,
                    timeout=self.ctx.timeout_tools,
                    verify=ssl,
                    )

            if response.status_code != 200:
                raise exceptions.CloudScraperError(
                        f"Status code: {response.status_code}"
                        )

            return response

        except Exception as e:
            raise exceptions.CloudScraperError(
                    f"{e.__class__.__name__}: {e}"
                    )

    def tool_googlecache(self) -> httpx.Response:
        """
        Use the Google Cache to fetch the website's historic data.

        :return: A response object if successful, otherwise exception.
        :rtype: httpx.Response | GoogleCacheError.
        :raises: GoogleCacheError.
        """

        raise NotImplementedError

        # WiP.
        # try:
        #     google_cache_url = \
        #         (f"http://webcache.googleusercontent.com/search?q=ca"
        #          f"che:{self.ctx.url}")
        #     with httpx.Client() as client:
        #         response = client.get(
        #                 url=google_cache_url,
        #                 timeout=self.ctx.timeout_tools,
        #                 follow_redirects=True,
        #                 )
        #
        #     if response.status_code != 200:
        #         raise exceptions.GoogleCacheError(
        #                 f"Status code: {response.status_code}"
        #                 )
        #
        #     return response
        #
        # except Exception as e:
        #     raise exceptions.GoogleCacheError(
        #             f"{e.__class__.__name__}: {e}"
        #             )

    def tool_selenium(self) -> httpx.Response:
        """
        Use the Selenium web driver to fetch the website's data.

        :return: A response object if successful, otherwise exception.
        :rtype: httpx.Response | SeleniumError.
        :raises: SeleniumError.
        """
        raise NotImplementedError

    def tool_waybackarchive(self) -> httpx.Response | object:
        """
        Use the Wayback Machine to fetch the website's historic data.

        :return: A response object if successful, otherwise exception.
        :rtype: httpx.Response | FakeResponse | WaybackArchiveError.
        :raises: WaybackArchiveError.
        """

        class FakeResponse:
            status_code = 200
            text = None

        ua = simple_header.sua.get(num=5, shuffle=True, force_cached=True)[
            0].string

        # Force a refresh of the website in archive (Cache refresh).
        try:
            save_api = waybackpy.WaybackMachineSaveAPI(url=self.ctx.url,
                                                       user_agent=ua,
                                                       max_tries=3,
                                                       )
            wayback_url = save_api.save()

            # Refresh did not work, use the CDX API to get the newest.
            if save_api.cached_save:
                raise waybackpy.exceptions.WaybackError

        # If this fails, we use the CDX API to get the newest version.
        except waybackpy.exceptions.WaybackError:
            cdx_api = waybackpy.WaybackMachineCDXServerAPI(url=self.ctx.url,
                                                           user_agent=ua,
                                                           max_tries=3,
                                                           )
            wayback_url = cdx_api.newest().archive_url

        # Fetch the website from the Wayback Machine.
        try:
            with httpx.Client() as client:
                response = client.get(
                        url=wayback_url,
                        timeout=self.ctx.timeout_tools,
                        follow_redirects=True,
                        )

            if response.status_code != 200:
                raise exceptions.WaybackArchiveError(
                        f"Status code: {response.status_code}"
                        )

            # We need to remove the Wayback header to get only the
            # original website's source code.
            wb_headers = ["<!-- END WAYBACK TOOLBAR INSERT -->",
                          "<!-- End Wayback Rewrite JS Include -->",
                          "<!--.*end.*wayback.*-->"]
            wb_footer = "FILE ARCHIVED ON"

            for wb_header in wb_headers:
                pattern = (f".*{re.escape(wb_header)}(.*?)"
                           f"{re.escape(wb_footer)}.*")
                match = re.search(pattern, response.text, re.IGNORECASE
                                  )

                if match:
                    # Convert the string to a fake response object for
                    # compatibility with the other services.
                    fake_response = FakeResponse()
                    fake_response.text = match.group(1).strip()
                    print("gab match:", fake_response.text)
                    return fake_response

            return response

        except Exception as e:
            raise exceptions.WaybackArchiveError(
                    f"{e.__class__.__name__}: {e}"
                    )


class ServiceManager:
    """
    This class manages the external scraping services and their APIs.
    All services are used to fetch the website's data.

    :ivar WebScraperContext ctx: The context object for shared settings
        and properties.
    """

    def __init__(self, ctx: WebScraperContext) -> None:
        """
        Initialize the ServiceManager object by passing the context
        object for shared settings and properties.

        :param ctx: Pass the context for shared instance attributes.
        :type ctx: WebScraperContext
        """
        self.ctx = ctx

    def service_dripcrawler(self) -> object:
        """
        Use the DripCrawler free API to fetch the website's data.

        :return: A response object if successful, otherwise exception.
        :rtype: FakeResponse | DripCrawlerFailedError.
        :raises: DripCrawlerFailedError.
        """

        class FakeResponse:
            status_code = 200
            text = None
            content = None

        # render = True -> enable JavaScript rendering.
        payload = {"url": self.ctx.url,
                   "javascript_rendering": "True"
                   }

        api_headers = {
                "content-type": "application/json",
                "X-RapidAPI-Key": const.API_KEY_DRIPCRAWLER,
                "X-RapidAPI-Host": "dripcrawler.p.rapidapi.com"
                }

        endpoint = "https://dripcrawler.p.rapidapi.com/"

        try:
            with httpx.Client() as client:
                response = client.post(
                        url=endpoint,
                        json=payload,
                        headers=api_headers,
                        timeout=self.ctx.timeout_services,
                        follow_redirects=True,
                        )

            if response.status_code != 200:
                raise exceptions.DripCrawlerFailedError(
                        f"Status code: {response.status_code}"
                        )

            # Convert the json response to a fake response object for
            # compatibility with the other services.
            fake_response = FakeResponse()
            fake_response.text = response.json()["extracted_html"]
            fake_response.content = fake_response.text

            return fake_response

        except (httpx.HTTPError, ConnectionError) as e:
            raise exceptions.DripCrawlerFailedError(
                    f"{e.__class__.__name__}: {e}"
                    )

    def service_scrapingant(self) -> httpx.Response:
        """
        Use the ScrapingAnt API to fetch the website's data.

        :return: A response object if successful, otherwise exception.
        :rtype: httpx.Response | ScrapingAntFailedError.
        :raises: ScrapingAntFailedError.
        """

        # Extract the proxy country from accept language header.
        countries_supp = ("BR", "CA", "CN", "CZ", "FR", "DE", "HK", "IN",
                          "ID", "IT", "IL", "JP", "NL", "PL", "RU", "SA", "SG",
                          "KR", "ES", "GB", "AE", "US", "VN")
        country = self.ctx.headers["Accept-Language"][3:5].upper()
        if country not in countries_supp:
            country = "US"

        endpoint = (f"https://api.scrapingant.com/v2/general?url="
                    f"{self.ctx.url_encoded}&x-api-key="
                    f"{const.API_KEY_SCRAPANT}&proxy_country={country}"
                    f"&return_page_source=true")

        try:
            with httpx.Client() as client:
                response = client.get(
                        url=endpoint,
                        timeout=self.ctx.timeout_services,
                        follow_redirects=True,
                        )

            if response.status_code != 200:
                raise exceptions.ScrapingAntFailedError(
                        f"Status code: {response.status_code}"
                        )

            return response

        except (httpx.HTTPError, ConnectionError) as e:
            raise exceptions.ScrapingAntFailedError(
                    f"{e.__class__.__name__}: {e}"
                    )

    def service_scrapeup(self) -> httpx.Response:
        """
        Use the ScrapeUp API to fetch the website's data.

        :return: A response object if successful, otherwise exception.
        :rtype: httpx.Response | ScrapeUpFailedError.
        :raises: ScrapeUpFailedError.
        """

        # render = True -> enable JavaScript rendering.
        payload = {"api_key": const.API_KEY_SCRAPEUP,
                   "url": self.ctx.url_encoded,
                   "render": True,
                   }

        endpoint = "http://api.scrapeup.com"

        try:
            with httpx.Client() as client:
                response = client.get(
                        url=endpoint,
                        params=payload,
                        timeout=self.ctx.timeout_services,
                        follow_redirects=True,
                        )

            if response.status_code != 200:
                raise exceptions.ScrapeUpFailedError(
                        f"Status code: {response.status_code}"
                        )

            return response

        except (httpx.HTTPError, ConnectionError) as e:
            raise exceptions.ScrapeUpFailedError(
                    f"{e.__class__.__name__}: {e}"
                    )


class WebScraper:
    # Class settings.
    timeout_connect = 10
    timeout_tools = 30
    timeout_services = 60

    def __init__(
            self,
            domain: str,
            force_services: bool = False,
            ):
        """
        Initialize the WebScraper object to start the scraping process.

        :param domain: Pass the domain of the website to be scraped.
        :type domain: str
        :param force_services: Pass True to only use external services.
        :type force_services: bool
        """

        # Create the context object for shared settings and properties.
        self.ctx = WebScraperContext()

        # Pass the class settings to the context object.
        self.ctx.timeout_connect = self.timeout_connect
        self.ctx.timeout_tools = self.timeout_tools
        self.ctx.timeout_services = self.timeout_services

        # Pass the input to the context object.
        self.ctx.domain = domain
        self.ctx.force_services = force_services

        # Create all manager and handler objects.
        self.cm = ConnectionManager(ctx=self.ctx)
        self.rh = ResponseHandler(ctx=self.ctx)
        self.tm = ToolManager(ctx=self.ctx)
        self.sm = ServiceManager(ctx=self.ctx)

        # Start the scraping process.
        try:
            self.response = self.start()

            self.soup = self.rh.soupify(response=self.response)

            self.success = True

        except exceptions.WebScraperException as e:
            LOGGER.error(f"Error while creating WebScra"
                         f"per: {e.__class__.__name__}: {e}"
                         )
            self.success = False

    def start(self):
        """
        Start the scraping process for the object.

        :return: A response object if successful, otherwise exception.
        :rtype: httpx.Response | NotScrapableError.
        :raises: NotScrapableError.
        """

        # 1. Try to connect to the website first using SSL, if that
        # fails, try without SSL. The corresponding url (http/s) and
        # headers will be set as instance attributes. Check for every
        # response, if it is flagged as phishing by Cloudflare.
        LOGGER.debug(f"Trying to connect to '{self.ctx.domain}' ...")
        response = self.cm.connect(domain=self.ctx.domain)
        self.response = response

        self.rh.cloudflare_flagged(response=response)
        LOGGER.info("Not flagged as phishing by CloudFlare.")

        # 2. Check from the response if the website is protected by
        # cloudflare. If so, we have several options to bypass it.
        if self.rh.cloudflare_check(response=response):
            LOGGER.info("The website is protected by CloudFlare.")

            # 2.1. Try local tool first: Cloudscraper.
            if not self.ctx.force_services:
                try:
                    LOGGER.info(
                            "Trying to bypass with Cloudscraper."
                            )
                    response = self.tm.tool_cloudscraper()
                    self.rh.cloudflare_flagged(response=response)
                except exceptions.CloudScraperError as e:
                    LOGGER.warning(f"{e.__class__.__name__}: {e}")

            # 2.2. Try external services. Choose the order of services
            # randomly to avoid overusing one service.
            services = [self.sm.service_scrapingant,
                        self.sm.service_scrapeup,
                        self.sm.service_dripcrawler]
            random.SystemRandom().shuffle(services)

            for i, service in enumerate(services, start=1):

                try:
                    # Try the service.
                    LOGGER.info(f"Trying to bypass with "
                                f"{service.__name__.split('_')[-1]} ({i}/3)."
                                )
                    response = service()

                    # If worked, check if the website is flagged as
                    # phishing by Cloudflare, do not catch (see below).
                    self.rh.cloudflare_flagged(response=response)
                    LOGGER.info("Success! And not flagged as phishing by "
                                "CloudFlare."
                                )
                    break

                except exceptions.ScrapingServicesError as e:
                    # Service failed, try next.
                    LOGGER.warning(f"{e.__class__.__name__}: {e}")
                    continue

                # We do not catch CloudFlareFlaggedError here, because
                # we want to break out of the loop and the whole
                # function if the website is flagged as phishing. We
                # catch it in the __init__ method.

            # 2.3. If all services failed, try with other tools.
            # else:
            #    response = self.tm.tool_waybackarchive()

            # ...

        if (not response) or (response.status_code != 200):
            raise exceptions.NotScrapableError(self.ctx.domain)

        # Final success: Save status and return response.
        self.success = True
        return response

    @classmethod
    def get(
            cls,
            domain: str,
            force_services: bool = False, ):
        """
        Convenience function to create a ready-to-go WebScraper object.
        Automatically starts the scraping process and returns the
        object with 'response' and 'soup' and 'success' as instance
        attributes.

        :param domain: Pass the domain of the website to be scraped.
        :type domain: str
        :param force_services: Pass True to only use external services.
        :type force_services: bool
        :return: A WebScraper object.
        :rtype: WebScraper
        """

        return cls(domain=domain, force_services=force_services)


get = WebScraper.get

#
# import time
# import pickle
# import httpx
#
#
# class ProxyRotator:
#     def __init__(self, offline_file):
#         self.proxies = []
#         self.waitlist = {}
#         self.offline_proxies = []
#         self.offline_file = offline_file
#
#     def check_proxy(self, proxy):
#         try:
#             response = httpx.get('http://httpbin.org/ip',
#                                  proxies={"http://": proxy, "https://":
#                                  proxy},
#                                  timeout=5
#                                  )
#             return response.status_code == 200
#         except:
#             return False
#
#     def fetch_proxies(self, proxies):
#         for proxy in proxies:
#             if self.check_proxy(proxy):
#                 self.proxies.append(proxy)
#             else:
#                 self.waitlist[proxy] = 1
#
#     def update_waitlist(self):
#         for proxy in list(self.waitlist.keys()):
#             if self.check_proxy(proxy):
#                 self.proxies.append(proxy)
#                 del self.waitlist[proxy]
#             else:
#                 self.waitlist[proxy] += 1
#                 if self.waitlist[proxy] > 5:
#                     self.offline_proxies.append(proxy)
#                     del self.waitlist[proxy]
#
#     def update_offline_proxies(self):
#         for proxy in self.offline_proxies:
#             if self.check_proxy(proxy):
#                 self.proxies.append(proxy)
#                 self.offline_proxies.remove(proxy)
#
#     def save_offline_proxies(self):
#         with open(self.offline_file, 'wb') as f:
#             pickle.dump(self.offline_proxies, f)
#
#     def load_offline_proxies(self):
#         if os.path.exists(self.offline_file):
#             with open(self.offline_file, 'rb') as f:
#                 self.offline_proxies = pickle.load(f)


if __name__ == "__main__":
    # Set log level to DEBUG for testing.
    # LOGGER.setLevel(logging.DEBUG)

    # 0532lx.com
    import time

    start = time.perf_counter()

    res = get(domain="0532lx.com")
    print(res)
    print("SUCCESS:", res.success)
    print("RESPONSE:", res.response)
    # print("SOUP:", res.soup)

    print("VORBEI")

    end = time.perf_counter()

    print(f"Time: {end - start}s")

    exit(0)

    lol = ("https://api.scrapingant.com/v2/general?url="
           "{SCRAPEURL}&x-api-key="
           "{APIKEY}&proxy_country={LANGUAGE}"
           "&return_page_source=true")

    lol2 = lol.format(SCRAPEURL="https://www.google.de",
                      APIKEY="123",
                      LANGUAGE="DE"
                      )
    print(lol2)

    url = "http://0532lx.com"
    dom = "0532lx.com"

    ua = simple_header.sua.get(num=1)[0]
    print("User-Agent:", ua)

    headers = simple_header.get_dict(url=url, user_agent=ua, seed=3)
    print("Headers:", headers)

    scraper = WebScraper(domain=dom)
    res = scraper.request(headers=headers)

    soup = BeautifulSoup(res.text, "html.parser")
    print(soup.prettify())

# TODO: für alle requests.get eine übergeordnete func schreiben,
#  die url entgegen nimmt, erstmal normalen request macht mit SSL und
#  user-agent und header, referer doch auf google oder so setzen,
#  cloudflare -> cloudscraper
#  wenn das nicht klappt, dann ohne SSL und mit allow_redirects und
#  user-agent, wenn das auch nicht klappt wegen z.B. ip-ban dann öffentlichen
#  proxy, wenn das auch nicht klappt, dann mit web scraper api (z.b.
#  scrapingbee usw), oder scrapy-splash,
#  oder mit stealth selenium (aber das ist sehr langsam, vielleicht auch erst
#  selenium
#  dann web-api scraper). dann google cache probieren. eventuell mit vpn/proxy?

# Resources:

# Headers: https://scrapfly.io/blog/how-to-avoid-web-scraping-blocking-headers/

# Google Cache: https://brightdata.de/blog/web-data-de/web-scraping-without
# -getting-blocked

# https://www.zenrows.com/blog/web-scraping-headers#referer

# Free Scraping API: https://rapidapi.com/markhorverse-markhorverse-default
# /api/dripcrawler

# https://scrapeops.io/web-scraping-playbook/web-scraping-without-getting
# -blocked/

# https://scrapeops.io/web-scraping-playbook/web-scraping-guide-header-user
# -agents/

# https://scrapeops.io/docs/fake-user-agent-headers-api/overview/

# https://scrapeops.io/python-web-scraping-playbook/python-fake-user-agents/

# https://www.zenrows.com/blog/stealth-web-scraping-in-python-avoid-blocking
# -like-a-ninja#full-set-of-headers

# https://docs.apify.com/academy/anti-scraping#:~:text=Header%20checking%E2
# %80%8B&text=The%20most%20commonly%20known%20header,
# are%20sometimes%20used%20as%20well.

# Paper: https://www.researchgate.net/profile/Ajay-Bale/publication
# /363669276_Web_Scraping_Approaches_and_their_Performance_on_Modern_Websites
# /links/63295be5071ea12e36487be1/Web-Scraping-Approaches-and-their
# -Performance-on-Modern-Websites.pdf
