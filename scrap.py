import argparse
import sys
from newspaper import Article
from pygooglenews import GoogleNews
import pymongo
from tqdm import tqdm
import logging  # Import the logging module
from newspaper.article import ArticleException
import requests.exceptions

EN_SEARCH_TERMS = [
    "scandal",
    "fraud",
    "trial",
    "court",
    "appeal",
    "charged",
    "allegation",
    "accused",
    "fined",
    "fine",
    "corruption",
    "attack",
    "leaked",
    "incident",
    "hack",
    "cyberattack",
    "money laundering",
    "misconduct",
    "sanction breach",
    "Panama Papers",
    "Pandora Papers",
    "Paradise Papers",
    "Luanda Leaks",
    "default",
    "insolvency",
    "suspension",
    "suspended",
    "default",
    "collapse",
    "bank run",
    "outlook",
    "confirms",
    "reaffirms",
    "downgrade",
    "negative",
    "positive",
    "stable",
    "supervision",
    "regulator",
    "non-performing",
    "undercapitalized",
    "ESG",
    "sustainability",
    "sustainable",
    "low-carbon",
    "green loans",
    "green finance",
    "SDG",
    "resettlement",
    "land-grabbing",
    "biodiversity",
    "investment",
    "invests",
    "import",
    "financing",
    "signed",
    "deal",
    "loan",
    "signs",
    "pre-export financing",
    "commodity financing",
    "trade commodity financing",
    "export flows"
]


# Constants
SEARCH_QUERY = "finance"
NUM_ARTICLES_TO_SCRAP = 10
MONGODB_URL = "mongodb://172.17.0.2:27017/"
DB_NAME = "gns_raw"
COLLECTION_NAME = "articles"

# Define a list of supported languages and their corresponding Google News language codes
SUPPORTED_LANGUAGES = {
    'EN': 'en',
    'FR': 'fr',
    'ES': 'es',
    # Add more languages and codes as needed
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
def scrap_articles(language_code, search_query):
    success = False  # Initialize a success flag
    try:
        # Define language and country mappings based on language_code
        language_mappings = {
            'EN': {'language': 'en-US', 'country': 'US'},
            'FR': {'language': 'fr', 'country': 'FR'},
            'ES': {'language': 'es', 'country': 'ES'},
            # Add more mappings as needed
        }

        language_info = language_mappings.get(language_code)
        if language_info:
            gn = GoogleNews(lang=language_info['language'], country=language_info['country'])

            # Use a single progress bar for the global scraping progress
            pbar = tqdm(total=NUM_ARTICLES_TO_SCRAP * len(EN_SEARCH_TERMS), desc="Scraping Progress", mininterval=1.0)

            data = []
            error_count = 0  # Initialize a count for errors

            for term in EN_SEARCH_TERMS:
                search_results = gn.search(term)  # Use the search term

                for entry in search_results['entries'][:NUM_ARTICLES_TO_SCRAP]:
                    try:
                        article = Article(entry['link'])
                        article.download()
                        article.parse()
                        data.append({
                            "Title": article.title,
                            "Source": entry.get('source', ''),
                            "Published Time": entry['published'],
                            "Article URL": entry['link'],
                            "Content": article.text,
                            "Language": language_code,
                            "Search Term": term  # Include the search term in the data
                        })
                        pbar.update(1)  # Increment the progress bar for each article scraped
                    except ArticleException as e:
                        error_count += 1
                        logging.error(f"ArticleException: {e}")
                        pbar.update(1)  # Increment the progress bar for errors
                    except requests.exceptions.HTTPError as e:
                        error_count += 1
                        logging.error(f"HTTPError (403 Forbidden): {e}")
                        pbar.update(1)  # Increment the progress bar for errors
                    except Exception as e:
                        error_count += 1
                        logging.error(f"An error occurred while processing an article: {e}")
                        pbar.update(1)  # Increment the progress bar for errors

            pbar.close()  # Close the progress bar

            if error_count > 0:
                print(f"Scraping completed with {error_count} errors. Check 'scraping_errors.log' for details.")
            else:
                success = True  # Set the success flag to True
                # Log a message only when no errors are encountered
                logging.error('No errors found during scraping.')

            return success, data
    except Exception as e:
        print(f"An error occurred during scraping: {e}")
        return False, None  # Return False for the success flag and None for data in case of an error



# Define the insert_data_into_mongodb function
def insert_data_into_mongodb(data):
    try:
        collection = connect_to_mongodb()
        inserted_count = 0  # Initialize the count of inserted documents
        ignored_count = 0  # Initialize the count of ignored (duplicate) documents

        if data:
            for article_data in data:
                # Check if an article with the same URL already exists
                existing_article = collection.find_one({"Article URL": article_data["Article URL"]})
                if not existing_article:
                    # If not found, insert the article
                    collection.insert_one(article_data)
                    inserted_count += 1  # Increment the count for each inserted document
                else:
                    ignored_count += 1  # Increment the count for each ignored (duplicate) document
            
            print(f"Inserted {inserted_count} unique documents into MongoDB.")
            print(f"Ignored {ignored_count} duplicate documents.")
        else:
            print("No data to insert into MongoDB.")
    except Exception as e:
        print(f"An error occurred while inserting data into MongoDB: {e}")


# Define the query_mongodb function
def query_mongodb():
    try:
        collection = connect_to_mongodb()
        cursor = collection.find()

        count = 0  # Initialize a count variable
        duplicate_count = 0  # Initialize a count for duplicate documents

        seen_urls = set()  # Create a set to store unique Article URLs

        for document in cursor:
            count += 1  # Increment the count for each document

            # Check if the Article URL is already seen (indicating a duplicate)
            if document.get("Article URL") in seen_urls:
                duplicate_count += 1
                print(f"Duplicate article found (URL: {document.get('Article URL')})")
            else:
                seen_urls.add(document.get("Article URL"))

            print("Title:", document.get("Title"))
            print("Source:", document.get("Source"))
            print("Published Time:", document.get("Published Time"))
            print("Article URL:", document.get("Article URL"))
            print("Language:", document.get("Language"))            # print("Content:")
            # print(document.get("Content")) #uncomment if  u wanna check article text scraped
            print("\n" + "=" * 50 + "\n")

        if count == 0:
            print("No articles found in the MongoDB collection.")
        else:
            print(f"Number of articles found in the MongoDB collection: {count}")
            print(f"Number of duplicate articles found: {duplicate_count}")

    except Exception as e:
        print(f"An error occurred while querying the database: {e}")

def main():
    parser = argparse.ArgumentParser(description="Scrape and manage data in MongoDB")
    parser.add_argument("--purge", action="store_true", help="Purge (clear) the MongoDB collection")
    parser.add_argument("--scrap", choices=SUPPORTED_LANGUAGES.keys(), help="Scrape data for a specific language")
    parser.add_argument("--query", action="store_true", help="Query the MongoDB collection")

    # Add the --help option as a default action
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    scraped_data = None  # Initialize scraped_data

    # Specify the log file name
    log_filename = 'scraping_errors.log'

    if args.scrap:
        # Configure the logger to append to the same log file when scraping
        logging.basicConfig(filename=log_filename, level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
        # Add a separator message at the beginning of scraping
        logging.error('=== Script Execution Start (Scraping) ===')

    if args.purge:
        purge_db()
        # Exit after purging without adding any messages
        sys.exit(0)

    if args.query:
        query_mongodb()
        # Exit after querying without adding any messages
        sys.exit(0)

    if args.scrap:
        language = args.scrap  # Get the selected language from the command line
        search_query = SEARCH_QUERY  # Default search query

        # Define specific search queries for each language
        if language == 'EN':
            search_query = "finance"
        elif language == 'ES':
            search_query = "instituciones financieras"
        elif language == 'FR':
            search_query = "institution financière"

        success, scraped_data = scrap_articles(language, search_query)

        if scraped_data:
            print(f"Scraped {len(scraped_data)} articles in {language}.")
            insert_option = input("Do you want to store the scraped data in the database? (yes/no): ").strip().lower()
            if insert_option == "yes":
                insert_data_into_mongodb(scraped_data)
            else:
                print("Scraped data not stored in the database.")

        # Add a separator message at the end of scraping
        logging.error('=== Script Execution End (Scraping) ===')

if __name__ == "__main__":
    main()
