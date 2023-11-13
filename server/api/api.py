#!/usr/bin/env python3

"""
api.py: TODO: Headline...

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
import logging
from datetime import datetime, timedelta
from functools import wraps

import jwt
from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from werkzeug.http import HTTP_STATUS_CODES
from werkzeug.middleware.proxy_fix import ProxyFix

from controller import controller
from secrets import secrets

# Child logger.
LOGGER = logging.getLogger(__name__)

# Initialize HTTP Basic and Token Authentication.
basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()

# Create the Flask application.
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1,
                        x_port=1
                        )


def generate_token(uuid, exp=1):
    """
    Generate a JWT token with a given UUID and expiration time.

    :param uuid: The UUID to be included in the token.
    :type uuid: str
    :param exp: The expiration time of the token in hours.
        Default: 1 hour.
    :type exp: int
    :return: A JWT token.
    :rtype: str
    """

    # Payload for the JWT token, to be signed with the API secret key,
    # to be unique for each user, and to expire in 1 hour by default.
    payload = {
            "uuid": uuid,
            "exp": datetime.utcnow() + timedelta(
                    hours=exp,
                    )
            }

    token = jwt.encode(payload, secrets.API_SECRET_KEY, algorithm="HS256")
    return token


def throttle(f):
    """
    Decorator function to throttle API calls.

    :param f: The function to be throttled.
    :type f: function
    :return: The throttled function.
    :rtype: function
    """

    last_call = None
    time_interval = 1 / secrets.API_THROTTLE

    @wraps(f)
    def wrapper(*args, **kwargs):
        """
        The wrapper function throttles requests from the same IP address
        to a maximum of one request per time_interval seconds. If a
        request is made within that interval, it will return an error
        message and HTTP status code 429 (Too Many Requests). Otherwise,
        it will call the function f with all arguments passed to
        wrapper.

        :param args: Pass a variable number of arguments to the function
        :param kwargs: Pass keyword-ed, variable-length argument list to
            a function.
        :return: Wrapped function
        """

        nonlocal last_call
        now = datetime.now()
        if last_call and now - last_call < timedelta(seconds=time_interval):
            LOGGER.debug(f"Throttling requests from {request.remote_addr}.")

            return auth_error(429,
                              "Please try again later."
                              )
        last_call = now
        return f(*args, **kwargs)

    return wrapper


@basic_auth.verify_password
def auth_password(username, password):
    """
    Verify the password for Basic Authentication.

    :param username: The username (UUID of the client).
    :type username: str
    :param password: The hashed API access password in secrets.py.
    :type password: str
    :return: The username if the password is correct, None otherwise.
    :rtype: str
    """

    if username and password == hashlib.sha256(secrets.API_ACCESS_KEY.encode()
                                               ).hexdigest():
        return str(username)


@app.route("/auth/login", methods=["POST"])
@basic_auth.login_required
@throttle
def auth_token():
    """
    Generate a token for a user, which is used for later authentication.

    :return: A JSON response containing the token.
    :rtype: flask.Response
    """

    uuid = basic_auth.current_user()
    token = generate_token(uuid)
    return jsonify({"token": token})


@token_auth.verify_token
def auth_verify(token):
    """
    Verify a token for Token Authentication.

    :param token: The token to be verified.
    :type token: str
    :return: The UUID from the token if it is valid, None otherwise.
    :rtype: str
    """

    try:
        token_dec = jwt.decode(token, secrets.API_SECRET_KEY,
                               algorithms=["HS256"]
                               )

    except Exception as e:
        LOGGER.error(f"Could not verify token: {str(e)}.")
        print("EXCEPTION:", str(e))
        return None

    # Check if the token is expired (e.g., expires in 1 hour).
    if datetime.utcnow() > datetime.fromtimestamp(token_dec["exp"]):
        # Block the request.
        return None

    return token_dec["uuid"]


# Error handling for unsupported requests.
@token_auth.error_handler
@basic_auth.error_handler
def auth_error(status_code, message=None):
    """
    Handle authentication, authorization, and general API errors.

    :param status_code: The HTTP status code.
    :type status_code: int
    :param message: The error message. Default is None.
    :type message: str
    :return: A JSON response containing the error.
    :rtype: flask.Response
    """

    payload = {"error": HTTP_STATUS_CODES.get(status_code, "Unknown error")}
    if message:
        payload["message"] = message
    response = jsonify(payload)
    response.status_code = status_code
    return response


@app.route("/analyze/ask", methods=["POST"])
@token_auth.login_required
@throttle
def analyze():
    """
    Analyze endpoint for plugin to send the domain to the backend.
    """

    data = request.get_json()

    # Extract the data from the request.
    domain = data.get("domain")

    # Forward the data to the controller.
    response_data = controller.analyze(domain)

    return jsonify(response_data), 200


# TODO: Implement endpoint to receive the user feedback from client.
@app.route("/analyze/feedback", methods=["POST"])
@token_auth.login_required
@throttle
def feedback():
    """
    The user can pass feedback (scam/trust) to the backend, which is
    used to re-calculate the score and improve the AI model.
    """

    data = request.get_json()

    # Extract the data from the request.
    domain = data.get("domain")
    user_feedback = data.get("user_feedback")

    # Forward the data to the controller.
    response_data = controller.feedback(domain, user_feedback)

    return jsonify({"message": "/analyze/feedback API route successfully "
                               f"called! Response data: {str(response_data)}"
                    }
                   )


def start():
    """
    The start function is the entry point to start the API.
    """

    # Start the Flask application.
    app.run(debug=True)
