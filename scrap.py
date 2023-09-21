import csv
from newspaper import Article
import pygooglenews
import pymongo

# Constants
SEARCH_QUERY = "banking industry partnership news"
NUM_ARTICLES_TO_SCRAPE = 10
MONGODB_URL = "mongodb://172.17.0.2:27017/"
DB_NAME = "gns_raw"
COLLECTION_NAME = "articles"

def scrape_articles():
    try:
        # Initialize Google News client
        gn = pygooglenews.GoogleNews()

        # Define your search query and get search results
        search_results = gn.search(SEARCH_QUERY)

        # Create a list to store the extracted data
        data = []

        # Iterate through the search results and scrape article content
        for entry in search_results['entries']:
            if len(data) >= NUM_ARTICLES_TO_SCRAPE:
                break

            try:
                article = Article(entry['link'])
                article.download()
                article.parse()

                # Extract relevant information from the article
                title = article.title
                source = entry['source']
                published_time = entry['published']
                article_url = entry['link']
                content = article.text

                # Append the data to the list
                data.append({
                    "Title": title,
                    "Source": source,
                    "Published Time": published_time,
                    "Article URL": article_url,
                    "Content": content
                })
            except Exception as e:
                print(f"An error occurred while processing an article: {e}")

        return data
    except Exception as e:
        print(f"An error occurred during scraping: {e}")

def insert_data_into_mongodb(data):
    try:
        # Establish a connection to the MongoDB server using a context manager
        with pymongo.MongoClient(MONGODB_URL) as client:
            # Select a database
            db = client[DB_NAME]

            # Create or select a collection
            collection = db[COLLECTION_NAME]

            # Use upsert to insert or update the data
            for item in data:
                # Define a filter to identify the document (assuming a unique key)
                filter = {"Title": item["Title"]}  # You can change the key as needed

                # Update or insert the document
                collection.update_one(filter, {"$set": item}, upsert=True)
    except Exception as e:
        print(f"An error occurred while inserting data into MongoDB: {e}")

# def query_mongodb():
#     try:
#         # Establish a connection to the MongoDB server using a context manager
#         with pymongo.MongoClient(MONGODB_URL) as client:
#             # Select the database and collection
#             db = client[DB_NAME]
#             collection = db[COLLECTION_NAME]

#             # Query and retrieve all documents (data) from the collection
#             cursor = collection.find({})

#             # Return the data as a list of dictionaries
#             return list(cursor)
#     except Exception as e:
#         print(f"An error occurred while querying the database: {e}")



# if __name__ == "__main__":
#     scraped_data = scrape_articles()
#     if scraped_data:
#         insert_data_into_mongodb(scraped_data)

#     retrieved_data = query_mongodb()

#     # Print the retrieved data
#     for item in retrieved_data:
#         print(item)

def query_mongodb():
    retrieved_data = []  # Initialize an empty list to store the data
    try:
        # Establish a connection to the MongoDB server using a context manager
        with pymongo.MongoClient(MONGODB_URL) as client:
            # Select the database and collection
            db = client[DB_NAME]
            collection = db[COLLECTION_NAME]

            # Query and retrieve all documents (data) from the collection
            cursor = collection.find({})

            # Iterate through the cursor, print each document, and append it to retrieved_data
            for document in cursor:
                print("Title:", document.get("Title"))
                # print("Source:", document.get("Source"))
                # print("Published Time:", document.get("Published Time"))
                # print("Article URL:", document.get("Article URL"))
                # print("\n" + "=" * 50 + "\n")  # Separating lines for readability

                # Append the document to the retrieved_data list
                retrieved_data.append({
                    "Title": document.get("Title"),
                    "Source": document.get("Source"),
                    "Published Time": document.get("Published Time"),
                    "Article URL": document.get("Article URL")
                })

    except Exception as e:
        print(f"An error occurred while querying the database: {e}")
    
    return retrieved_data  # Return the retrieved data as a list


if __name__ == "__main__":
    scraped_data = scrape_articles()
    if scraped_data:
        insert_data_into_mongodb(scraped_data)

    retrieved_data = query_mongodb()

    # Check if retrieved_data is not None
    if retrieved_data:
        # Print the number of items found in the MongoDB collection
        print(f"Number of items found in the MongoDB collection: {len(retrieved_data)}")
    else:
        print("No data found in the MongoDB collection.")

def purge_db():
    try:
        # Establish a connection to the MongoDB server using a context manager
        with pymongo.MongoClient(MONGODB_URL) as client:
            # Select the database
            db = client[DB_NAME]

            # Select the collection
            collection = db[COLLECTION_NAME]

            # Delete all documents in the collection
            result = collection.delete_many({})

            # Print the number of documents deleted
            print(f"Purged {result.deleted_count} documents from the collection.")
    except Exception as e:
        print(f"An error occurred while purging the database: {e}")
