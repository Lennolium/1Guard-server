from bs4 import BeautifulSoup
import requests


def has_valid_trustedshops_certificate(domain: str) -> bool:
    resp = requests.get(
        f"https://www.trustedshops.de/shops/?q={domain}&hasValidCertificate=true"
    )

    soup = BeautifulSoup(resp.content, "html.parser")
    for heading in soup.select("h3"):
        if domain in heading.text:
            return True
    return False


print(has_valid_trustedshops_certificate("123homeoffice.at"))
