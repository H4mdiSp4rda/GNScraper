import os
import argparse
import sys
from mongo_ops import purge_db, insert_data_into_mongodb, query_mongodb
from newspaper import Article, Config
from pygooglenews import GoogleNews
from bs4 import BeautifulSoup
import requests
import pymongo
from tqdm import tqdm
import logging
from urllib3.exceptions import NewConnectionError
from newspaper.article import ArticleException
import random
import time
from fake_useragent import UserAgent

# Constants
NUM_ARTICLES_TO_SCRAP = 5
max_retries = 3
retry_delay = 5
user_agent = UserAgent()


# Define the LANGUAGE_CONFIG dictionary
LANGUAGE_CONFIG = {
    'fr': {
        "search_terms": ["scandale", "fraude"], # add international banks search terms
        "countries": ["FR", "SN"],
        "language": "fr",
    },
    'ar': {
        "search_terms": ["فضيحة", "احتيال"],
        "countries": ["EG", "AE"],
        "language": "ar",
    },
}


def extract_link(url):
    user_agent = UserAgent().random
    headers = {'User-Agent': user_agent}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        try:
            link = soup.find('a', jsname='tljFtd')['href']
            #print(link)
            return link
        except TypeError:
            logging.basicConfig(filename='scraping_errors.log', level=logging.ERROR)
            logging.error(f"Error extracting link from {url}")
            return None
    else:
        print(f"Response returned status code {response.status_code}")
        sleep_time = random.randint(1, 6)
        print(f"Sleeping for {sleep_time} seconds...")
        time.sleep(sleep_time)
        return extract_link(url)

# Define the scrap_articles function
def scrap_articles(language_code, search_query, insert_method, country, debug_mode=False):
    try:
        language_info = LANGUAGE_CONFIG.get(language_code)
        if language_info:
            gn = GoogleNews(lang=language_info['language'], country=country)

            search_results = gn.search(search_query)
            data = []

            # Extract the country code from the country variable
            country_code = country.split()[0]

            for entry in tqdm(search_results['entries'][:NUM_ARTICLES_TO_SCRAP], desc=f"Scraping {country_code} ({search_query.split()[0]})", mininterval=1.0):
                if debug_mode:
                    # Print the country, language, and search term being scraped
                    print(f"Scraping: Country - {country}, Language - {language_code}, Search Term - {search_query.split()[0]}")

                article_link = None  # Initialize article_link to None

                for retry_count in range(max_retries):
                    try:
                        headers = {
                            'User-Agent': user_agent.random,  # Set the User-Agent header
                            'Referer': 'https://www.google.com/',
                            # Add other headers if needed
                        }
                        config = Config()
                        config.headers = headers
                        config.request_timeout = 6

                        # Extract the article link using the extract_link function
                        article_link = extract_link(entry['link'])
                        # Download the article using NewsPlease
                        article = Article(article_link, config=config)
                        article.download()
                        article.parse()

                        # Check if the article is valid
                        if article is not None:
                            data.append({
                                "Title": article.title,
                                "Source": entry.get('source', ''),
                                "Published Time": entry['published'],
                                "Article URL": article_link,
                                "Content": article.text,
                                "Language": language_code,
                                "Country": country
                            })
                        break  # Successful request, exit the retry loop
                    except requests.exceptions.HTTPError as e:
                        logging.error(f"HTTPError ({e.response.status_code} {e.response.reason}): {e}")
                    except ConnectionError as e:
                        logging.error(f"ConnectionError: {e}")
                        if retry_count < max_retries - 1:
                            logging.info(f"Retrying the request in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                        else:
                            logging.error("Max retries reached. Skipping the article.")
                            break  # Max retries reached, exit the retry loop
                    except Exception as e:
                        logging.error(f"An error occurred while processing '{article_link}': {e}")

                time.sleep(random.uniform(1, 3))

            if insert_method == "auto":
                insert_data_into_mongodb(data, country)
            else:
                insert_option = input("Do you want to store the scraped data in the database? (yes/no): ").strip().lower()
                if insert_option == "yes":
                    insert_data_into_mongodb(data, country)

    except Exception as e:
        logging.error(f"An error occurred during scraping for {country}: {e}")

# Define the main function
def main():
    parser = argparse.ArgumentParser(description="Scrape news articles, manage data, and store it in MongoDB.")

    # Add arguments
    parser.add_argument("--purge", action="store_true", help="Clear all documents from the MongoDB collection.")
    parser.add_argument("--scrap", nargs=2, metavar=('LANGUAGE', 'INSERT_METHOD'),
                        help="Scrape news articles for a specific language and specify the insertion method. "
                             "Example: --scrap FR auto or --scrap AR auto.")
    parser.add_argument("--query", action="store_true", help="Query and display documents in the MongoDB collection.")
    # Add the --help option as a default action
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    scraped_data = None  # Initialize scraped_data

    log_filename = './logs/scrap logs/scraping_errors.log'  # Save log file in a 'logs' directory in the current working directory

    # Check if the directory exists
    if not os.path.exists('logs'):
        # If the directory doesn't exist, create it
        os.makedirs('logs')


    logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info('=== Script Execution Start (Scraping) ===')  # Log script start

    if args.purge:
        purge_db()
        # Exit after purging without adding any messages
        sys.exit(0)

    if args.query:
        query_mongodb()
        # Exit after querying without adding any messages
        sys.exit(0)

    if args.scrap:
        language, insert_method = args.scrap
        language = language.lower()  # Convert the language to lowercase for the scrap_articles function
        if insert_method not in ["auto", "manual"]:
            print("Error: The insert_method must be 'auto' or 'manual'.")
            sys.exit(1)

        language_config = LANGUAGE_CONFIG.get(language)

        if language_config:
            countries = language_config["countries"]
            gn = GoogleNews(lang=language_config['language'], country=countries[0])

            for country in countries:
                for search_term in language_config["search_terms"]:
                    search_query = f"{search_term} {country}"
                    scraped_data = scrap_articles(language, search_query, insert_method, country)

                    if scraped_data:
                        print(f"Scraped {len(scraped_data)} articles in {language} for search term '{search_term}' and country '{country}'.")

    logging.info('=== Script Execution End (Scraping) ===')  # Log script end

if __name__ == "__main__":
    main()
