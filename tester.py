import argparse
import sys
import logging
from newspaper import Article
import pymongo
from tqdm import tqdm
import requests.exceptions

# Define search terms for different regions
SEARCH_TERMS = {
    'fr-FR': ["scandale", "fraude"],
    'fr-SN': ["scandale", "fraude"],
    'ar-EG': ["فضيحة", "احتيال"],
    'ar-AE': ["فضيحة", "احتيال"],
}

# Constants
NUM_ARTICLES_TO_SCRAP = 10
MONGODB_URL = "mongodb://localhost:27017/"
DB_NAME = "gns_raw"
COLLECTION_NAME = "articles"

# Language mapping for regions
language_mapping = {
    "fr": ["fr-FR", "fr-SN"],
    "ar": ["ar-EG", "ar-AE"],
}

# Connect to MongoDB and return the collection
def connect_to_mongodb():
    client = pymongo.MongoClient(MONGODB_URL)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    return collection

# Purge (clear) the MongoDB collection
def purge_db():
    try:
        collection = connect_to_mongodb()
        result = collection.delete_many({})
        print(f"Purged {result.deleted_count} documents from the collection.")
    except Exception as e:
        print(f"An error occurred while purging the database: {e}")

# Scrape articles for a given language and search terms
def scrap_articles(language):
    try:
        regions = language_mapping.get(language, [])
        if not regions:
            print(f"No regions defined for language: {language}")
            return

        gn = Article()

        scraped_data = []
        error_count = 0

        for region_code in regions:
            search_terms = SEARCH_TERMS.get(region_code, [])

            for term in search_terms:
                gn.set_language(region_code)
                search_results = gn.search(term, num=NUM_ARTICLES_TO_SCRAP)

                for entry in search_results:
                    try:
                        article = Article(entry.link)
                        article.download()
                        article.parse()
                        scraped_data.append({
                            "Title": article.title,
                            "Source": entry.source,
                            "Published Time": entry.published,
                            "Article URL": entry.link,
                            "Content": article.text,
                            "Region": region_code,
                            "Search Term": term,
                        })
                    except ArticleException as e:
                        error_count += 1
                        logging.error(f"ArticleException: {e}")
                    except requests.exceptions.HTTPError as e:
                        error_count += 1
                        logging.error(f"HTTPError (403 Forbidden): {e}")
                    except Exception as e:
                        error_count += 1
                        logging.error(f"An error occurred while processing an article: {e}")

        if error_count > 0:
            print(f"Scraping completed with {error_count} errors. Check 'scraping_errors.log' for details.")
        else:
            print(f"Scraped {len(scraped_data)} articles for language: {language}")

        return scraped_data
    except Exception as e:
        print(f"An error occurred during scraping: {e}")
        return []



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

        for _ in cursor:
            count += 1  # Increment the count for each document

        cursor.rewind()  # Rewind the cursor to the beginning for printing

        for document in cursor:
            print("Title:", document.get("Title"))
            print("Source:", document.get("Source"))
            print("Published Time:", document.get("Published Time"))
            print("Article URL:", document.get("Article URL"))
            print("Language:", document.get("Language"))  # Print the Language field
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
