import requests
from bs4 import BeautifulSoup


def get_trustpilot_data(url: str) -> dict:
    """
    Given a domain, return the relevant data from Trustpilot used for calculating a score.

    :param url: url (with a prefix http or https) of the website. May or may not contain the "www." prefix.
    :return: A dictionary
    :rtype: dict

    Format: {
        "average_rating": "4.5",
        "total_ratings": "1234",
        "contact_information": "
            Company Name
            Street 123
            12345 City
            Country
        ",
        "reviews": [
            {
                "title": "Title of the review",
                "text": "Text of the review"
            },
            {
                "title": "Title of the review",
                "text": "Text of the review"
            },
            ...
        ]
    }
    """

    SELECTORS = {
        "AVERAGE_RATING": "span.typography_heading-m__T_L_X.typography_appearance-default__AAY17",
        "TOTAL_RATINGS": "p[data-reviews-count-typography='true']",
        "CONTACT_INFORMATION": ".typography_body-m__xgxZ_.typography_appearance-default__AAY17.styles_contactInfoAddressList__RxiJI",
    }

    domain = url.split("//")[-1].split("/")[0]
    if not domain.startswith("www."):
        domain = "www." + domain

    def __get_page_content(page: int):
        """
        Fetch the content of one single page, described by the page number, starting from 1.
        """
        response = requests.get(
            f"https://www.trustpilot.com/review/{domain}?page={page}"
        )
        if response.status_code == 200:
            return response.text
        else:
            return None

    def __get_basic_information():
        """
        Fetch all the basic information, which is the same on every page.

        :return: A dictionary
        :rtype: dict

        Format: {
            "average_rating": "4.5",
            "total_ratings": "1234",
            "contact_information": "
                Company Name
                Street 123
                12345 City
                Country
            ",
        }
        """
        soup = BeautifulSoup(__get_page_content(page=1), "html.parser")

        average_rating = soup.select_one(SELECTORS["AVERAGE_RATING"]).text
        total_ratings = (
            soup.find("p", {"data-reviews-count-typography": "true"})
            .text.replace(" total", "")
            .replace(",", "")
            .replace(".", "")
        )
        contact_information = ""
        for line in soup.select_one(SELECTORS["CONTACT_INFORMATION"]).findAll("li"):
            contact_information += line.text + "\n"

        return {
            "average_rating": average_rating,
            "total_ratings": total_ratings,
            "contact_information": contact_information,
        }

    def __get_all_reviews():
        """
        Fetch all the reviews from all pages.

        :return: A list of dictionaries
        :rtype: list[dict]

        Format: [
            {
                "title": "Title of the review",
                "text": "Text of the review"
            },
            {
                "title": "Title of the review",
                "text": "Text of the review"
            },
            ...
        ]
        """

        def __get_reviews_on_one_page(soup: BeautifulSoup):
            all_reviews = []
            for review in soup.findAll(
                "article", {"data-service-review-card-paper": "true"}
            ):
                title = review.find(
                    "h2", {"data-service-review-title-typography": "true"}
                ).text
                text = review.find(
                    "p", {"data-service-review-text-typography": "true"}
                ).text
                all_reviews.append(
                    {
                        "title": title,
                        "text": text,
                    }
                )
            return all_reviews

        page = 1
        all_reviews = []

        while True:
            html = __get_page_content(page=page)
            if not html:
                break
            soup = BeautifulSoup(html, "html.parser")
            new_reviews = __get_reviews_on_one_page(soup)
            all_reviews += new_reviews
            page += 1

            if len(new_reviews) < 20:
                break
        return all_reviews

    basic_information = __get_basic_information()
    return basic_information | {
        "reviews": __get_all_reviews(),
    }


def get_score(url: str) -> int:
    """
    Given a domain, return the score calculated from the data from Trustpilot.

    :param url: url (with a prefix http or https) of the website. May or may not contain the "www." prefix.
    :return: A score between 0 and 15.
    :rtype: int
    """
    data = get_trustpilot_data(url)

    # TODO: implement score calculation given the data
