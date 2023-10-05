import argparse
import sys
from newspaper import Article
from pygooglenews import GoogleNews
import pymongo
from tqdm import tqdm
import logging
from urllib3.exceptions import NewConnectionError
from newspaper.article import ArticleException
import requests.exceptions
import random
import time
from fake_useragent import UserAgent  # You need to install the 'fake-useragent' package

# Constants
NUM_ARTICLES_TO_SCRAP = 50
max_retries = 3
retry_delay = 5
user_agent = UserAgent()
MONGODB_URL = "mongodb://172.17.0.2:27017/"
DB_NAME = "gns_raw"
COLLECTION_NAME = "articles"

# Define the LANGUAGE_CONFIG dictionary
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

# Create a MongoDB client and select the database and collection
def connect_to_mongodb():
    client = pymongo.MongoClient(MONGODB_URL)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    return collection

# Define the purge_db function
def purge_db():
    try:
        collection = connect_to_mongodb()
        result = collection.delete_many({})
        print(f"Purged {result.deleted_count} documents from the collection.")
    except Exception as e:
        print(f"An error occurred while purging the database: {e}")

# Define the scrap_articles function
def scrap_articles(language_code, search_query, insert_method, country, debug_mode=True):
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

                for retry_count in range(max_retries):
                    try:
                        headers = {
                            'User-Agent': user_agent.random,
                            'Referer': 'https://www.google.com/',
                        }

                        article = Article(entry['link'], headers=headers)
                        article.download()
                        article.parse()
                        data.append({
                            "Title": article.title,
                            "Source": entry.get('source', ''),
                            "Published Time": entry['published'],
                            "Article URL": entry['link'],
                            "Content": article.text,
                            "Language": language_code,
                            "Country": country
                        })
                        break  # Successful request, exit the retry loop
                    except ArticleException as e:
                        logging.error(f"ArticleException: {e}")
                        break  # No need to retry if it's an ArticleException
                    except requests.exceptions.HTTPError as e:
                        logging.error(f"HTTPError ({e.response.status_code} {e.response.reason}): {e}")
                    except NewConnectionError as e:
                        logging.error(f"NewConnectionError: {e}")
                        if retry_count < max_retries - 1:
                            logging.info(f"Retrying the request in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                        else:
                            logging.error("Max retries reached. Skipping the article.")
                            break  # Max retries reached, exit the retry loop
                    except Exception as e:
                        logging.error(f"An error occurred while processing '{entry['link']}': {e}")

                time.sleep(random.uniform(1, 3))

            if insert_method == "auto":
                insert_data_into_mongodb(data, country)
            else:
                insert_option = input("Do you want to store the scraped data in the database? (yes/no): ").strip().lower()
                if insert_option == "yes":
                    insert_data_into_mongodb(data, country)

    except Exception as e:
        logging.error(f"An error occurred during scraping for {country}: {e}")


# Define the insert_data_into_mongodb function
def insert_data_into_mongodb(data, country):
    try:
        collection = connect_to_mongodb()
        inserted_count = 0
        ignored_count = 0

        if data:
            for article_data in data:
                article_url = article_data["Article URL"]

                existing_article = collection.find_one({"Article URL": article_url})
                if not existing_article:
                    collection.insert_one(article_data)
                    inserted_count += 1
                else:
                    ignored_count += 1

            print(f"Scraped {len(data)} articles for {country}.")
            print(f"Inserted {inserted_count} unique documents into MongoDB.")
            print(f"Ignored {ignored_count} duplicate documents.")
        else:
            print(f"No articles scraped for {country}.")

    except Exception as e:
        print(f"An error occurred while inserting data into MongoDB for {country}: {e}")


# Define the query_mongodb function
def query_mongodb():
    try:
        collection = connect_to_mongodb()
        cursor = collection.find()

        count = 0  # Initialize a count variable

        for _ in cursor:
            count += 1  # Increment the count for each document

        cursor.rewind()  # Rewind the cursor to the beginning for printing

        for document in cursor:
            print("Title:", document.get("Title"))
            print("Source:", document.get("Source"))
            print("Published Time:", document.get("Published Time"))
            print("Article URL:", document.get("Article URL"))
            print("Language:", document.get("Language"))  # Print the Language field
            print("Country:", document.get("Country"))
            # print("Content:")
            # print(document.get("Content")) #uncomment if  u wanna check article text scraped
            print("\n" + "=" * 50 + "\n") ##uncomment if  u wanna check article text scraped

        if count == 0:
            print("No articles found in the MongoDB collection.")
        else:
            print(f"Number of articles found in the MongoDB collection: {count}")

    except Exception as e:
        print(f"An error occurred while querying the database: {e}")

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

    # Specify the log file name
    log_filename = 'scraping_errors.log'
    
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
