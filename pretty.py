import argparse
import logging
import time
import requests.exceptions
from bs4 import BeautifulSoup
import urllib.parse

MAX_ARTICLES_TO_SCRAP = 2
LOG_FILE = 'scraper.log'
SLEEP_DURATION = 2

logging.basicConfig(filename=LOG_FILE, level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

LANGUAGE_CONFIG = {
    'fr': {
        "search_terms": ["scandale", "fraude"],
        "countries": ["FR", "SN"],
        "language": "fr",
    },
    'ar': {
        "search_terms": ["فضيحة", "احتيال"],
        "countries": ["EG", "AE"],
        "language": "ar",
    },
}

def scrape_articles(language):
    if language not in LANGUAGE_CONFIG:
        print(f"Language '{language}' not supported.")
        return

    config = LANGUAGE_CONFIG[language]
    search_terms = config["search_terms"]
    countries = config["countries"]

    for term in search_terms:
        for country in countries:
            print(f"Scraping: Language: {language}, Country: {country}, Search Term: {term}")
            articles_scrapped = 0
            error_count = 0

            while articles_scrapped < MAX_ARTICLES_TO_SCRAP:
                try:
                    base_url = "https://news.google.com"
                    url = f"{base_url}/search?q={term}&hl={language}&gl={country}"
                    response = requests.get(url)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Find all 'article' elements
                    result_articles = soup.select("article")

                    # Iterate through the 'article' elements
                    for article in result_articles:
                        try:
                            # Extract title
                            title = article.find('h3').get_text()

                            # Extract source
                            source_element = article.find('div', class_='vr1PYe')
                            source = source_element.get_text() if source_element else "N/A"
                            # Extract link
                            link_element = article.find('a', class_='VDXfz')
                            link = link_element.get('href') if link_element else "N/A"
                            full_link = urllib.parse.urljoin(base_url, link) if link != "N/A" else "N/A"

                            # Extract datetime
                            datetime_element = article.find('time')
                            raw_datetime = datetime_element.get('datetime') if datetime_element else "N/A"

                            # Extract date and remove time
                            if raw_datetime != "N/A":
                                date_parts = raw_datetime.split("T")
                                date = date_parts[0]
                            else:
                                date = "N/A"

                            # Print the details
                            print(f"Title: {title}")
                            print(f"Source: {source}")
                            print(f"URL: {full_link}")
                            print(f"Date/Time: {date}\n")

                            # Follow the link to the full article and extract the article body
                            if full_link != "N/A":
                                full_response = requests.get(full_link)
                                full_response.raise_for_status()
                                full_soup = BeautifulSoup(full_response.text, 'html.parser')
                                article_body = full_soup.find('div', class_='article-body')  # Adjust the selector as needed
                                if article_body:
                                    article_text = article_body.get_text()
                                    print(f"Article Body:\n{article_text}\n")

                            articles_scrapped += 1
                            time.sleep(SLEEP_DURATION)

                            if articles_scrapped >= MAX_ARTICLES_TO_SCRAP:
                                break
                        except Exception as e:
                            print(f"An error occurred while processing an article: {e}")

                except requests.exceptions.RequestException as e:
                    error_count += 1
                    logging.error(f"RequestException: {e}")
                except Exception as e:
                    error_count += 1
                    logging.error(f"An error occurred while processing: {e}")

                if error_count >= 3:
                    print("Too many errors, stopping scraping.")
                    break

            # Print or use the extracted information as needed.

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape articles from Google News")
    parser.add_argument("--scrape", type=str, help="Language to scrape (e.g., 'fr' or 'ar')")
    args = parser.parse_args()

    if args.scrape:
        scrape_articles(args.scrape)
    else:
        print("Please specify a language to scrape using the --scrape argument.")
