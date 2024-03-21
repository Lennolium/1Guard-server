#!/usr/bin/env python3

"""
fetch_data.py: TODO: Headline...

TODO: Description...
"""

# Header.
__author__ = "Lennart Haack"
__email__ = "lennart-haack@mail.de"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__date__ = "2023-11-24"
__status__ = "Prototype/Development/Production"

# Imports.
# from bs4 import BeautifulSoup
#
# import requests
#
#
# def send_request():
#     response = requests.get(
#             url='https://app.scrapingbee.com/api/v1/',
#             params={
#                     'api_key':
#                         'YLFZR401LKN92C58E3KOYFDC6KB3M5NI950A1VKM1CIHQO7IGXCY0APL949QCHSWEVUIED0P0OS29ED3',
#                     'url': 'https://www.virustotal.com/gui/domain/chicladdy'
#                            '.com/detection',
#                     'wait': '5000',
#                     'json_response': 'true',
#                     },
#
#             )
#     print('Response HTTP Status Code: ', response.status_code)
#     # print('Response HTTP Response Body: ', response.content)
#
#     for key in response.json()['xhr']:
#         # print(key)
#
#         for key2 in key:
#             # print(key2)
#
#             # print("--------------------" * 10)
#
#             # separate each dict
#             # print(key[key2])
#
#             if key[key2] == (
#             "https://www.virustotal.com/ui/domains/chicladdy"
#                              ".com"):
#                 print("FOUND IT")
#                 # print(key)
#
#                 body = key['body']
#
#                 popularity = body["data"]["attributes"]["popularity_ranks"]
#
#                 print(popularity)
#
#                 print(body)
#
#             # print("--------------------" * 10)
#
#     # soup = BeautifulSoup(response.content, 'html.parser')
#
#     # print(soup.prettify())
#
#
# send_request()
#
# exit(0)
#
# # Imports.
# # import time
# #
# # import asyncio
# # from playwright.async_api import async_playwright
#
# # url = "https://www.forloop.ai/blog"
# #
# #
# # async def run(playwright):
# #     browser = await playwright.chromium.launch()
# #     context = await browser.new_context()
# #
# #     # Open a new page
# #     page = await context.new_page()
# #
# #     # Navigate to the forloop.ai blog page
# #     await page.goto(url)
# #
# #     # Find all articles
# #     articles = await page.query_selector_all('div.article-item')
# #
# #     # Extract titles, tags, and dates
# #     for item in articles:
# #         title_element = await item.query_selector('h4')
# #         title = await title_element.inner_text()
# #
# #         tag_element = await item.query_selector('div.text-white')
# #         tag = await tag_element.inner_text()
# #
# #         date_element = await item.query_selector('div.blog-post-date')
# #         date = await date_element.inner_text()
# #
# #         print(f'Title: {title}\\nTag: {tag}\\nDate: {date}\\n---')
# #
# #     # Close the browser
# #     await browser.close()
# #
# #
# # # Run the function
# # async def main():
# #     await run(async_playwright())
# #
# #
# # exit(0)
#
# import requests_html
#
# a_page_url = "https://www.virustotal.com/gui/domain/chicladdy.com"
# # a_page_url = "https://pythonclock.org"
#
# session = requests_html.HTMLSession()
#
# session.headers.update({
#         "x-app-version": "v1x233x0",
#         "x-tool": "vt-ui-main",
#         "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ("
#                       "KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
#         "content-type": "application/json",
#         "accept": "application/json",
#         "referer": "https://www.virustotal.com/",
#         "accept-ianguage": "en-US,en;q=0.9,es;q=0.8",
#         "x-vt-anti-abuse-header":
#             "MTc3NTcxMzM4NDQtWkc5dWRDQmlaU0JsZG1scy0xNzAxMzQ0NzUyLjgyNw==",
#         "cookie": "_ga=GA1.2.611293565.1701344753; "
#                   "_gid=GA1.2.1897613847.1701344753; _gat=1"
#         }
#         )
#
# r = session.get(a_page_url)
#
# r.html.render(timeout=10, sleep=10)
#
# # rendering = r.html.html
#
# lol = (r.html.html)
#
# from bs4 import BeautifulSoup
#
# soup = BeautifulSoup(lol, 'html.parser')
#
# print(soup.prettify())
#
# # exit(0)
#
# # from bs4 import BeautifulSoup
# #
# # from playwright.sync_api import sync_playwright
# #
# # with sync_playwright() as p:
# #     for browser_type in [p.firefox, ]:  # p.chromium, p.webkit]:
# #         browser = browser_type.launch(headless=True)
# #         context = browser.new_context()
# #         page = context.new_page()
# #         page.goto("https://www.virustotal.com/gui/domain/chicladdy.com",
# #                   wait_until="networkidle"
# #                   )
# #
# #         # page.wait_for_selector('div')
# #         page.wait_for_load_state("domcontentloaded")
# #
# #         html = page.content()
# #         soup = BeautifulSoup(html, 'html.parser')
# #         print(soup.prettify())
# #
# #         page.screenshot(path=f'example-{browser_type.name}.png',
# #                         full_page=True
# #                         )
# #         browser.close()
# #
# # sync_playwright()
# #
# # exit(0)
# # #
# # from requests_html_playwright.requests_html import HTMLSession
# #
# # domain = "https://pythonclock.org"
# # domain = "https://www.virustotal.com/gui/domain/chicladdy.com"
# #
# # session = HTMLSession()
# #
# # # simulate a browser by browser agent
# # session.headers.update({
# #         'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
# #                       'AppleWebKit/537.36 (KHTML, like Gecko) '
# #                       'Chrome/91.0.4472.114 Safari/537.36'
# #         }
# #         )
# #
# # # Simulate to the website that javascript is activated
# # session.browser_args = [
# #         '--disable-gpu',
# #         '--disable-dev-shm-usage',
# #         '--disable-setuid-sandbox',
# #         '--no-first-run',
# #         '--no-sandbox',
# #         '--no-zygote',
# #         '--single-process'
# #         ]
# #
# # r = session.get(domain)
# #
# # r.html.render()
# #
# # # searched = r.html.search('Python 2.7 will retire in...{}Enable Guido
# # # Mode')[0]
# #
# # soup = BeautifulSoup(r.html.html, 'html.parser')
# #
# # print(soup.prettify())
