#!/usr/bin/env python3

"""
database.py: TODO: Headline...

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
import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from pymongo import MongoClient, errors

# Child logger.
LOGGER = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages connections and operations for the MongoDB database.

    :param db_url: The URL of the MongoDB database
    :type db_url: str
    :param db_name: The name of the database
    :type db_name: str
    :param db_collection: The name of the collection in the database
    :type db_collection: str
    """

    def __init__(self, db_url: str,
                 db_name: str,
                 db_collection: str,
                 ) -> None:
        """
        Initializes the DatabaseManager with the specified database URL,
        name, and collection, along with an optional TLS certificate.

        :param db_url: The URL of the MongoDB database
        :type db_url: str
        :param db_name: The name of the database
        :type db_name: str
        :param db_collection: The name of the collection in database
        :type db_collection: str
        """

        self.client = MongoClient(db_url)

        # Check if server is available, ping does not require auth.
        try:
            self.client.admin.command('ping')
            LOGGER.debug("Successfully connected to MongoDB server.")
        except errors.ConnectionFailure as e:
            LOGGER.error("Could not connect to MongoDB server. Error: "
                         f"{str(e)}"
                         )

        self.db = self.client[db_name]
        self.collection = self.db[db_collection]

    def insert_entry(self, data: dict) -> None:

        """
        The insert_entry function takes a dictionary as an argument and
        inserts it into the database. It also adds two keys to the
        dictionary: created_at and updated_at, which are both set to
        datetime.now().

        :param self: Represent the instance of the class
        :param data: dict: Pass in the data that will be inserted into
            the database
        :return: None
        """

        now = datetime.now()
        data["created_at"] = now
        data["updated_at"] = now
        self.collection.insert_one(data)

        LOGGER.debug(f"Inserted entry into database: {data}")

    def update_entry(self, data: dict) -> None:
        """
        The update_entry function updates the entry for a given domain
        with the specified data. It also updates the updated_at key to
        the actual time.

        :param self: Represent the instance of the class
        :param data: dict: Pass in the data that will be updated
        :return: None
        """

        now = datetime.now()
        data["updated_at"] = now
        domain = data.get("domain")
        self.collection.update_one(
                {"domain": domain},
                {"$set": data}
                )

        LOGGER.debug(f"Updated entry into database: {data}")

    def get_by_uuid(self, uuid: str) -> dict:
        """
        Retrieves data from the MongoDB collection based on UUID.

        :param uuid: The UUID of the data to be retrieved
        :type uuid: str
        :return: The retrieved data from the collection
        :rtype: dict
        """

        return self.collection.find_one({"uuid": uuid})

    def get_by_domain(self, domain: str) -> dict:
        """
        Retrieves data from the MongoDB collection based on domain.

        :param domain: The domain of the data to be retrieved
        :type domain: str
        :return: The retrieved data from the collection
        :rtype: dict
        """

        return self.collection.find_one({"domain": domain})

    def close_connection(self) -> None:
        """
        Closes the connection to the MongoDB database.
        """

        self.client.close()
        LOGGER.debug("Closed connection to MongoDB server ...")


class WebsiteScore(ABC):
    """
    Abstract base class representing a website score.

    :param domain: The domain of the website
    :type domain: str
    :param score: The score of the website
    :type score: int
    :param user_score: The user score of the website
    :type user_score: int
    :param category: The category of the website
    :type category: str
    """

    def __init__(self, domain: str, score: int, user_score: int, category: str
                 ) -> None:
        """
        Initializes the WebsiteScore with the specified domain, score,
        user score, and category.

        :param domain: The domain of the website
        :type domain: str
        :param score: The score of the website
        :type score: int
        :param user_score: The user score of the website
        :type user_score: int
        :param category: The category of the website
        :type category: str
        """

        self.uuid: str = str(uuid.uuid4())
        self.domain: str = domain
        self.score: int = score
        self.score_readable: str = self._convert_scores(score)
        self.user_score: int = user_score
        self.user_score_readable: str = self._convert_scores(user_score)
        self.category: str = category  # e.g. "fraud", "phishing" ...

    @abstractmethod
    def to_dict(self) -> dict:
        """
        The to_dict function returns a dictionary representation of the
        object. ABC (abstract base class) is used to make sure that the
        function is implemented in the child class.

        :param self: Refer to the current instance of the class
        :return: A dictionary representation of the object
        :rtype: dict
        """

        pass

    @staticmethod
    def _convert_scores(score: int) -> str:
        """
        Converts the numerical score to a corresponding letter grade.

        :param score: The numerical score of the website
        :type score: int
        :return: The corresponding letter grade
        :rtype: str
        """

        grades: dict = {
                0: "F",
                1: "E-",
                2: "E",
                3: "E+",
                4: "D-",
                5: "D",
                6: "D+",
                7: "C-",
                8: "C",
                9: "C+",
                10: "B-",
                11: "B",
                12: "B+",
                13: "A-",
                14: "A",
                15: "A+"
                }
        return grades.get(score, "Unknown")


class WebsiteScoreEntry(WebsiteScore):
    """
    Represents an entry of the website score.

    :param domain: The domain of the website
    :type domain: str
    :param score: The score of the website
    :type score: int
    :param user_score: The user score of the website
    :type user_score: int
    :param category: The category of the website
    :type category: str
    """

    def __init__(self, domain: str, score: int, user_score: int, category: str
                 ) -> None:
        """
        Initializes the WebsiteScoreEntry with the specified domain, score,
        user score, and category.

        :param domain: The domain of the website
        :type domain: str
        :param score: The score of the website
        :type score: int
        :param user_score: The user score of the website
        :type user_score: int
        :param category: The category of the website
        :type category: str
        """

        super().__init__(domain, score, user_score, category)

    def to_dict(self) -> dict:
        """
        The to_dict function is used to convert the object into a
        dictionary. This is necessary to store the object in the
        database,  while maintaining the object's attributes.

        :param self: Represent the instance of the class
        :return: A dictionary of the object's attributes
        :rtype: dict
        """

        return {
                "uuid": self.uuid,
                "domain": self.domain,
                "category": self.category,
                "score": self.score,
                "score_readable": self.score_readable,
                "user_score": self.user_score,
                "user_score_readable": self.user_score_readable,
                }
