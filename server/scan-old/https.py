#!/usr/bin/env python3

"""
https.py: TODO: Headline...

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
import socket
from datetime import datetime

import requests
from OpenSSL import SSL

# Child logger.
LOGGER = logging.getLogger(__name__)


def check_https(domain):
    try:
        context = SSL.Context(SSL.SSLv23_METHOD)
        sock = socket.create_connection((domain, 443))
        connection = SSL.Connection(context, sock)
        connection.set_connect_state()
        connection.set_tlsext_host_name(domain.encode())
        connection.do_handshake()
        cert = connection.get_peer_certificate()

        # Get certificate details
        common_name = cert.get_subject().commonName
        ssl_version = connection.get_protocol_version_name()
        issuer = cert.get_issuer().CN
        expiry_date = datetime.strptime(cert.get_notAfter().decode("ascii"),
                                        "%Y%m%d%H%M%SZ"
                                        )
        signature_algorithm = cert.get_signature_algorithm().decode("ascii")

        return {
                "ssl_version": ssl_version,
                "common_name": common_name,
                "issuer": issuer,
                "expiry_date": expiry_date,
                "signature_algorithm": signature_algorithm
                }

    # No HTTPS enabled (insecure).
    except Exception as e:
        print(f"Error: {str(e)}")
        return None


def check_security_headers(domain):
    """
    The check_security_headers function takes a domain as an argument
    and returns a dictionary of the security headers that are present on
    the website.

    Security headers are a group of headers in the HTTP response sent by
    the web server to the browser. These headers aim to enhance the
    security of the website by enabling browser security policies. You
    can check if a website has implemented security headers by sending a
    request to the site and checking the headers in the response.

    HSTS:
        HSTS is a web security policy mechanism that helps to protect
    websites against protocol downgrade attacks and cookie hijacking.
    You can check if a website has implemented HSTS by sending a request
    to the site and checking the headers in the response for the
    Strict-Transport-Security header.
    -> Good: True

    Secure Cookies:
        Secure cookies are a type of HTTP cookie that have the secure
    attribute enabled. This means they can only be transmitted over an
    encrypted HTTPS connection. You can check if a website is using
    secure cookies by sending a request to the site and checking the
    Set-Cookie headers in the response.
    -> Good: True

    CSP:
        CSP is an added layer of security that helps to detect and mitigate
    certain types of attacks, including Cross Site Scripting (XSS) and
    data injection attacks. You can check if a website has implemented
    CSP by sending a request to the site and checking the headers in the
    response for the Content-Security-Policy header.
    -> Good: True

    X-Content-Type-Options:
        The X-Content-Type-Options response HTTP header is a marker used by
    the server to indicate that the MIME types advertised in the
    Content-Type headers should not be changed and be followed. This
    allows to opt-out of MIME type sniffing, or, in other words, it is a
    way to say that the webmasters knew what they were doing.
    -> Good: True


    X-Frame-Options:
        The X-Frame-Options HTTP response header can be used to indicate
    whether a browser should be allowed to render a page in a <frame>,
    <iframe>, <embed> or <object>. Sites can use this to avoid
    clickjacking attacks, by ensuring that their content is not embedded
    into other sites.
    -> Good: True



    :param domain: Pass in the domain name of the website
    :return: A dictionary
    :rtype: dict
    """

    # Send request to the website and get the headers and cookies.
    response = requests.get(f"https://{domain}")
    headers = response.headers
    cookies = response.cookies

    # List of security headers to check.
    security_headers = [
            "strict-transport-security",  # HSTS
            "content-security-policy",  # CSP
            "x-content-type-options",  # X-Content-Type-Options
            "x-frame-options",  # X-Frame-Options
            ]

    result = {}

    # Check if the headers are present.
    for header in security_headers:
        if header in headers:
            result[header] = True
        else:
            result[header] = False

    # Check if the cookies are secure (HTTPS only).
    result["secure-cookies"] = all(cookie.secure for cookie in cookies)

    return result


def check_category(domain):
    """
    The check_category function takes a domain as an argument and
    returns the category of the website.

    :param domain: Pass in the domain name of the website
    :return: A string
    :rtype: str
    """

    # TODO: Implement the category finder.
    return "Jewelry"


if __name__ == "__main__":

    # Negative test case (No HTTPS/SSL):
    website_domain = "http.badssl.com/"
    # Positive test case (HTTPS/SSL):
    # website_domain = "github.com"

    https_info = check_https(website_domain)
    if https_info:
        print("HTTPS/SSL enabled for this website. Good!")
        print(https_info)
    else:
        print("No HTTPS/SSL enabled for this website. Very insecure!")

    security_headers = check_security_headers(website_domain)
    print(security_headers)
