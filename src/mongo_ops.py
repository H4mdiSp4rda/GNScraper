import pymongo

# Define variables for MongoDB username, password, host, and port
MONGODB_USERNAME = "admin"
MONGODB_PASSWORD = "admin"
MONGODB_HOST = "172.22.0.8"
MONGODB_PORT = "27017"
DB_NAME = "gns_mongodb"
COLLECTION_NAME = "articles"

# Construct the MongoDB URI with host, port, username, and password
MONGODB_URL = f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/"


def connect_to_mongodb():
    client = pymongo.MongoClient(MONGODB_URL)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    return collection

def purge_db():
    try:
        collection = connect_to_mongodb()
        result = collection.delete_many({})
        print(f"Purged {result.deleted_count} documents from the collection.")
    except Exception as e:
        print(f"An error occurred while purging the database: {e}")

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
            print(f"No articles scraped for {country}")

    except Exception as e:
        print(f"An error occurred while inserting data into MongoDB for {country}: {e}")

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
            print("Content:")
            print(document.get("Content"))
            print("\n" + "=" * 50 + "\n")

        if count == 0:
            print("No articles found in the MongoDB collection.")
        else:
            print(f"Number of articles found in the MongoDB collection: {count}")

    except Exception as e:
        print(f"An error occurred while querying the database: {e}")
