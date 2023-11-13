#!/usr/bin/env python3

"""
plugin.py: TODO: Headline...

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
import hashlib
import uuid

import requests

from secrets import secrets

# API_LOGIN_URL = "http://127.0.0.1:5000/auth/login"
# API_ANALYZE_URL = "http://127.0.0.1:5000/analyze/ask"
# API_FEEDBACK_URL = "http://127.0.0.1:5000/analyze/feedback"

API_LOGIN_URL = "https://1guard.vercel.app/auth/login"
API_ANALYZE_URL = "https://1guard.vercel.app/analyze/ask"
API_FEEDBACK_URL = "https://1guard.vercel.app/analyze/feedback"


def api_login():
    # Authorization by login with username (uuid) and api password.
    try:
        # Hash the API access key.
        password = hashlib.sha256(
                secrets.API_ACCESS_KEY.encode()
                ).hexdigest()
        username = uuid.getnode()

        response = requests.post(API_LOGIN_URL, auth=(username,
                                                      password)
                                 )

        if response.status_code == 200:
            response_data = response.json()
            token = response_data.get("token", None)

            return token

        else:
            print("Request failed with status code:", response.status_code,
                  response.text
                  )
            return

    except requests.exceptions.RequestException as e:
        print("Request failed with error:", e)
        return


def api_analyze(data, token):
    try:
        # Authorization by passing the token in the header (needed
        # for every request).
        headers = {'Authorization': f'Bearer {token}'}

        response = requests.post(API_ANALYZE_URL, headers=headers,
                                 json=data
                                 )

        if response.status_code == 200:
            response_data = response.json()

            return response_data

        else:
            print("Request failed with status code:", response.status_code,
                  response.text
                  )
            return

    except requests.exceptions.RequestException as e:
        print("Request failed with error:", e)
        return


def api_feedback(data, token):
    try:
        # Authorization by passing the token in the header (needed
        # for every request).
        headers = {'Authorization': f'Bearer {token}'}

        response = requests.post(API_FEEDBACK_URL, headers=headers,
                                 json=data
                                 )

        if response.status_code == 200:
            response_data = response.json()

            return response_data

        else:
            print("Request failed with status code:", response.status_code,
                  response.text
                  )
            return

    except requests.exceptions.RequestException as e:
        print("Request failed with error:", e)
        return


# Mockup plugin code to test the API.
def plugin_mockup(domain):
    # Login to the API and get a token.
    token = api_login()
    print("Received token from /auth/login API:")
    print(token)

    # Analyze the domain and passing the token for authorization.
    # Example data to send to the API.
    data = {"domain": domain}
    response = api_analyze(data, token)
    print("Received data from /analyze/ask API:")
    print(response)

    data2 = {"domain": domain,
             "user_feedback": "scam"
             }
    response2 = api_feedback(data2, token)
    print("Received data from /analyze/feedback API:")
    print(response2)


if __name__ == "__main__":
    plugin_mockup("example.com")
