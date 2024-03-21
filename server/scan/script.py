#!/usr/bin/env python3

"""
script.py: TODO: Headline...

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
import requests

from oneguardai import const


def statusbar_mouseover(response: requests.Response) -> bool:
    """
    This function checks if JavaScript is used to show a fake URL in the
    status bar to users.

    :param response: Pass the response object of the site to be checked
    :return: True if the domain is using JavaScript to show a fake URL
    """

    if const.MOUSEOVER_RE.findall(response.text):
        return True

    else:
        return False


def rightclick_disabled(response: requests.Response) -> bool:
    """
    This function checks if JavaScript is used to disable
    right-clicking, so that users cannot view the page source.

    :param response: Pass the response object of the site to be checked
    :return: True if JavaScript is used to disable right-clicking
    """

    if const.RIGHT_CLICK_RE.findall(response.text):
        return True

    else:
        return False


def popup_window(response: requests.Response) -> bool:
    """
    This function checks if the websites asks the user to click on a
    link or button to close a popup window or to enter his credentials.

    :param response: Pass the response object of the site to be checked
    :return: True if a popup appears
    """

    if const.POPUP_RE.findall(response.text):
        return True

    else:
        return False


def i_frame(response: requests.Response) -> bool:
    """
    This function checks the HTML tag used to display additional web
    pages in the current website. A phisher will take advantage of it by
    making the tag invisible without a frame border.

    :param response: Pass the response object of the site to be checked
    :return: True if used
    """

    if const.I_FRAME_RE.findall(response.text):
        return True

    else:
        return False
