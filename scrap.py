import argparse
from newspaper import Article
from pygooglenews import GoogleNews
import pymongo

# Constants
SEARCH_QUERY = "finance"
NUM_ARTICLES_TO_SCRAP = 50
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
def scrap_articles(language_code):
    try:
        country_code = 'US'  # Default country code to 'US'
        
        if language_code == 'FR':
            country_code = 'FR'  # Set country code to 'FR' for French
        elif language_code == 'ES':
            country_code = 'ES'  # Set country code to 'ES' for Spanish

        gn = GoogleNews(lang=language_code, country=country_code)
        search_results = gn.search(SEARCH_QUERY)
        data = []

        for entry in search_results['entries'][:NUM_ARTICLES_TO_SCRAP]:
            try:
                article = Article(entry['link'])
                article.download()
                article.parse()
                data.append({
                    "Title": article.title,
                    "Source": entry['source'],
                    "Published Time": entry['published'],
                    "Article URL": entry['link'],
                    "Content": article.text
                })
            except Exception as e:
                print(f"An error occurred while processing an article: {e}")

        return data
    except Exception as e:
        print(f"An error occurred during scraping: {e}")

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
            print("Content:")
            # print(document.get("Content")) #uncomment if  u wanna check article text scraped
            # print("\n" + "=" * 50 + "\n") ##uncomment if  u wanna check article text scraped

        if count == 0:
            print("No articles found in the MongoDB collection.")
        else:
            print(f"Number of articles found in the MongoDB collection: {count}")

    except Exception as e:
        print(f"An error occurred while querying the database: {e}")

# ...

def main():
    global SEARCH_QUERY  # Declare SEARCH_QUERY as global

    parser = argparse.ArgumentParser(description="Scrape and manage data in MongoDB")
    parser.add_argument("--purge", action="store_true", help="Purge (clear) the MongoDB collection")
    parser.add_argument("--scrap", choices=SUPPORTED_LANGUAGES.keys(), help="Scrape data for a specific language")
    parser.add_argument("--query", action="store_true", help="Query the MongoDB collection")

    args = parser.parse_args()
    scraped_data = None  # Initialize scraped_data

    if args.purge:
        purge_db()

    if args.scrap:
        language = args.scrap  # Get the selected language from the command line
        google_news_language_code = SUPPORTED_LANGUAGES.get(language)
        if google_news_language_code:
            scraped_data = scrap_articles(google_news_language_code)
            if scraped_data:
                print(f"Scraped {len(scraped_data)} articles in {language}.")
                insert_option = input("Do you want to store the scraped data in the database? (yes/no): ").strip().lower()
                if insert_option == "yes":
                    insert_data_into_mongodb(scraped_data)
                else:
                    print("Scraped data not stored in the database.")
        else:
            print("Selected language is not supported.")

    if args.query:
        query_mongodb()

if __name__ == "__main__":
    main()
