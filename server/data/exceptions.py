#!/usr/bin/env python3

"""
exceptions.py: Our custom exceptions for the web scraper.

Hierarchy:

* WebScraperException(Exception)

  x WebsiteError
    + NotReachableError
    + NotScrapableError
    + CloudflareFlaggedError

  x ScrapingToolsError
    + SeleniumError
    + CloudScraperError
    + BeautifulSoupError

  x ScrapingServicesError
    + ScrapingAntFailedError
    + ScrapeUpFailedError
    + DripCrawlerFailedError

"""

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__date__ = "2024-02-09"
__status__ = "Prototype/Development/Production"


# Imports.


class WebScraperException(Exception):
    """
    Base class for exceptions in this module.
    """


class WebsiteError(WebScraperException):
    """
    Base class for exceptions related to websites.
    """


class NotReachableError(WebsiteError):
    """
    Website is not reachable and probably offline.
    """


class NotScrapableError(WebsiteError):
    """
    Website is not scrapable because of various anti-scraping
    techniques.
    """


class CloudflareFlaggedError(WebsiteError):
    """
    Website is flagged as phishing by Cloudflare, and thus we can not
    access it.
    """


class ScrapingToolsError(WebScraperException):
    """
    Base class for exceptions related to internal scraping tools.
    """


class SeleniumError(ScrapingToolsError):
    """
    Selenium failed to fetch the website.
    """


class CloudScraperError(ScrapingToolsError):
    """
    CloudScraper (CloudFlare bypass) failed to fetch the website.
    """


class GoogleCacheError(ScrapingToolsError):
    """
    Google Cache failed because no historic version of the website
    could be found.
    """


class WaybackArchiveError(ScrapingToolsError):
    """
    Wayback Machine failed because no historic version of the website
    could be found or a cache refresh is failed.
    """


class BeautifulSoupError(ScrapingToolsError):
    """
    BeautifulSoup failed to parse the website.
    """


class ScrapingServicesError(WebScraperException):
    """
    Base class for exceptions related to external scraping services.
    """


class ScrapingAntFailedError(ScrapingServicesError):
    """
    ScrapingAnt service failed to fetch the website.
    """


class ScrapeUpFailedError(ScrapingServicesError):
    """
    ScrapeUp service failed to fetch the website.
    """


class DripCrawlerFailedError(ScrapingServicesError):
    """
    DripCrawler free service failed to fetch the website.
    """
