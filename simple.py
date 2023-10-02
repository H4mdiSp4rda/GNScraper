import argparse
import logging
from pygooglenews import GoogleNews
from newspaper import Article
import time

MAX_ARTICLES_TO_SCRAP = 10  # Edit this constant to set the maximum number of articles to scrap
LOG_FILE = 'scraper.log'  # Specify the log file name

# Configure logging
logging.basicConfig(filename=LOG_FILE, level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

LANGUAGE_CONFIG = {
    'fr': {
        "search_terms": ["scandale", "fraude"],
        "countries": ["fr-FR", "fr-SN"],
        "language": "fr",
    },
    'ar': {
        "search_terms": ["فضيحة", "احتيال"],
        "countries": ["ar-EG", "ar-AE"],
        "language": "ar",
    },
}

def scrap_articles(language):
    if language not in LANGUAGE_CONFIG:
        print(f"Language '{language}' not supported.")
        return

    config = LANGUAGE_CONFIG[language]
    search_terms = config["search_terms"]
    countries = config["countries"]
    for term in search_terms:
        for country in countries:
            print(f"Scraping: Language: {language}, Country: {country}, Search Term: {term}")
            gn = GoogleNews(lang=language, country=country)
            search_results = gn.search(term)
            articles_scrapped = 0
            for result in search_results['entries']:
                if articles_scrapped >= MAX_ARTICLES_TO_SCRAP:
                    break  # Stop scraping if the maximum number of articles has been reached
                try:
                    url = result['link']
                    article = Article(url)
                    article.download()
                    article.parse()
                    print(f"Title: {article.title}")
                    print(f"Published Date: {article.publish_date}")
                    # print(f"Content:\n{article.text}")
                    print("\n" + "=" * 50 + "\n")
                    articles_scrapped += 1
                    time.sleep(2)  # Add a delay to avoid overloading Google News
                except Exception as e:
                    # Log the error and continue with the next article
                    error_message = f"Error while processing URL {url}: {str(e)}"
                    print(error_message)
                    logging.error(error_message)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrap articles from Google News")
    parser.add_argument("--scrap", type=str, help="Language to scrap (e.g., 'fr' or 'ar')")
    args = parser.parse_args()

    if args.scrap:
        scrap_articles(args.scrap)
    else:
        print("Please specify a language to scrap using the --scrap argument.")
