from bs4 import BeautifulSoup
import requests
from fake_useragent import UserAgent
import logging

url = "https://news.google.com/rss/articles/CBMiwgFodHRwczovL3d3dy5vdWVzdC1mcmFuY2UuZnIvc3BvcnQvZm9vdGJhbGwvZXF1aXBlLWl0YWxpZS92aWRlby1waXJsby1zdXItbGUtc2NhbmRhbGUtZGVzLXBhcmlzLWRvbW1hZ2UtZGUtZ2FjaGVyLXNhLWNhcnJpZXJlLWV0LXNvbi10YWxlbnQtcG91ci1jZXMtY2hvc2VzLWxhLTA1MmFiMzYyLTE2NTYtM2ExZC04ODdjLTNlNzFlMzU0MzQ4M9IBAA"


def extract_link(url):
    user_agent = UserAgent().random
    headers = {'User-Agent': user_agent}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        try:
            link = soup.find('a', jsname='tljFtd')['href']
            print(link)
            return link
        except TypeError:
            logging.basicConfig(filename='scraping_errors.log', level=logging.ERROR)
            logging.error(f"Error extracting link from {url}")
            return None
    else:
        return f"Response returned status code {response.status_code}"

extract_link(url)
