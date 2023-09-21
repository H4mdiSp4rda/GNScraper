import argparse
from newspaper import Article
import pygooglenews
import pymongo

# Constants
SEARCH_QUERY = "banking industry partnership news"
NUM_ARTICLES_TO_SCRAP = 10
MONGODB_URL = "mongodb://172.17.0.2:27017/"
DB_NAME = "gns_raw"
COLLECTION_NAME = "articles"

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
def scrap_articles():
    try:
        gn = pygooglenews.GoogleNews()
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

# Create a function to handle command-line arguments
def main():
    parser = argparse.ArgumentParser(description="Scrape and manage data in MongoDB")
    parser.add_argument("--purge", action="store_true", help="Purge (clear) the MongoDB collection")
    parser.add_argument("--scrap", action="store_true", help="Scrape data")
    parser.add_argument("--query", action="store_true", help="Query the MongoDB collection")

    args = parser.parse_args()
    scraped_data = None  # Initialize scraped_data

    if args.purge:
        purge_db()

    if args.scrap:
        scraped_data = scrap_articles()
        if scraped_data:
            print(f"Scraped {len(scraped_data)} articles.")
            insert_option = input("Do you want to store the scraped data in the database? (yes/no): ").strip().lower()
            if insert_option == "yes":
                insert_data_into_mongodb(scraped_data)
            else:
                print("Scraped data not stored in the database.")

    if args.query:
        query_mongodb()

if __name__ == "__main__":
    main()

