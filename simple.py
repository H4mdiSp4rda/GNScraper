import argparse
from newspaper import Config, Article
import requests.exceptions

MAX_ARTICLES_TO_SCRAP = 2

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


def scrape_articles(language):
    config = Config()
    config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'

    for term in LANGUAGE_CONFIG[language]["search_terms"]:
        for country in LANGUAGE_CONFIG[language]["countries"]:
            print(f"Scraping: Language: {language}, Country: {country}, Search Term: {term}")
            articles_scrapped = 0

            while articles_scrapped < MAX_ARTICLES_TO_SCRAP:
                try:
                    url = f"https://news.google.com/search?q={term}&hl={language}&gl={country}"
                    article = Article(url, config=config)
                    article.download()
                    article.parse()

                    # Extract title, source, URL, and date from the article
                    title = article.title
                    source = article.source_url
                    url = article.url
                    date = article.publish_date.strftime('%Y-%m-%d') if article.publish_date else "N/A"

                    # Print the details
                    print(f"Title: {title}")
                    print(f"Source: {source}")
                    print(f"URL: {url}")
                    print(f"Date: {date}\n")

                    articles_scrapped += 1

                except requests.exceptions.RequestException as e:
                    print(f"RequestException: {e}")
                except Exception as e:
                    print(f"An error occurred while processing: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape articles from Google News")
    parser.add_argument("--scrape", type=str, help="Language to scrape (e.g., 'fr' or 'ar')")
    args = parser.parse_args()

    if args.scrape:
        scrape_articles(args.scrape)
    else:
        print("Please specify a language to scrape using the --scrape argument.")
