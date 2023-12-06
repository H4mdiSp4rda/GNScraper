from gevent import monkey
monkey.patch_all(thread=False, select=False)

import pymongo
import sys
import subprocess
import datetime
import shutil  # Import the shutil module to find the full path of the mongodump and mongorestore commands

# MongoDB Atlas Configuration
MONGODB_ATLAS_USERNAME = "Sp4rda"
MONGODB_ATLAS_PASSWORD = "CuIHqKlU8dFzZ4zt"
MONGODB_ATLAS_CLUSTER = "gns-db"
MONGODB_ATLAS_DB_NAME = "gns_mongodb"
MONGODB_ATLAS_URI = f"mongodb+srv://{MONGODB_ATLAS_USERNAME}:{MONGODB_ATLAS_PASSWORD}@{MONGODB_ATLAS_CLUSTER}.g93kgy3.mongodb.net/{MONGODB_ATLAS_DB_NAME}?retryWrites=true&w=majority"
COLLECTION_NAME = "articles"

# MongoDB Docker Container Configuration
DOCKER_CONTAINER_USERNAME = "admin"
DOCKER_CONTAINER_PASSWORD = "admin"
DOCKER_CONTAINER_HOST = "172.16.238.10"
DOCKER_CONTAINER_PORT = "27017"
DOCKER_CONTAINER_DB_NAME = "gns_mongodb"
DOCKER_CONTAINER_URI = f"mongodb://{DOCKER_CONTAINER_USERNAME}:{DOCKER_CONTAINER_PASSWORD}@{DOCKER_CONTAINER_HOST}:{DOCKER_CONTAINER_PORT}/{DOCKER_CONTAINER_DB_NAME}"

def connect_to_mongo_atlas():
    try:
        client = pymongo.MongoClient(MONGODB_ATLAS_URI)
        db = client[MONGODB_ATLAS_DB_NAME]
        collection = db[COLLECTION_NAME]
        return collection
    except Exception as e:
        print(f"An error occurred while connecting to MongoDB Atlas: {e}")
        return None

def connect_to_mongo_container():
    try:
        client = pymongo.MongoClient(DOCKER_CONTAINER_URI)
        db = client[DOCKER_CONTAINER_DB_NAME]
        collection = db[COLLECTION_NAME]
        return collection
    except Exception as e:
        print(f"An error occurred while connecting to MongoDB Docker container: {e}")
        return None



def is_duplicate(collection, article_link, published_time):
    existing_article = collection.find_one({
        "Article URL": article_link,
        "Published Time": published_time
    })
    return existing_article is not None

def purge_db():
    try:
        collection = connect_to_mongo_atlas()
        result = collection.delete_many({})
        print(f"Purged {result.deleted_count} documents from the collection.")
    except Exception as e:
        print(f"An error occurred while purging the database: {e}")

def insert_data_into_mongodb(data, country):
    try:
        collection = connect_to_mongo_atlas()
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
        collection = connect_to_mongo_atlas()
        cursor = collection.find()

        count = 0  # Initialize a count variable

        for _ in cursor:
            count += 1  # Increment the count for each document

        cursor.rewind()  # Rewind the cursor to the beginning for printing

        for document in cursor:
            print("Title:", document.get("Title"))
            print("Translated Title:", document.get("Translated Title"))
            print("Source:", document.get("Source"))
            print("Published Time:", document.get("Published Time"))
            print("Article URL:", document.get("Article URL"))
            print("Language:", document.get("Language"))  
            print("Country:", document.get("Country"))
            print("Original Content:")
            print(document.get("Content") + "\n")
            print("Translated Content:")
            print(document.get("Translated Content"))
            print("\n" + "=" * 50 + "\n")

        if count == 0:
            print("No articles found in the MongoDB collection.")
        else:
            print(f"Number of articles found in the MongoDB collection: {count}")

    except Exception as e:
        print(f"An error occurred while querying the database: {e}")

def query_dockerDB():
    try:
        # Connect to MongoDB Docker container
        collection = connect_to_mongo_container()

        cursor = collection.find()

        count = 0  # Initialize a count variable

        for _ in cursor:
            count += 1  # Increment the count for each document

        cursor.rewind()  # Rewind the cursor to the beginning for printing

        for document in cursor:
            print("Title:", document.get("Title"))
            print("Translated Title:", document.get("Translated Title"))
            print("Source:", document.get("Source"))
            print("Published Time:", document.get("Published Time"))
            print("Article URL:", document.get("Article URL"))
            print("Language:", document.get("Language"))
            print("Country:", document.get("Country"))
            print("Original Content:")
            print(document.get("Content") + "\n")
            print("Translated Content:")
            print(document.get("Translated Content"))
            print("\n" + "=" * 50 + "\n")

        if count == 0:
            print("No articles found in the MongoDB Docker container.")
        else:
            print(f"Number of articles found in the MongoDB Docker container: {count}")

    except Exception as e:
        print(f"An error occurred while querying the MongoDB Docker container: {e}")

def get_mongodump_path():
    try:
        # Use shutil to find the full path of mongodump
        mongodump_path = shutil.which("mongodump")
        if not mongodump_path:
            raise FileNotFoundError("mongodump not found.")
        return mongodump_path
    except Exception as e:
        raise e

def get_mongorestore_path():
    try:
        # Use shutil to find the full path of mongorestore
        mongorestore_path = shutil.which("mongorestore")
        if not mongorestore_path:
            raise FileNotFoundError("mongorestore not found.")
        return mongorestore_path
    except Exception as e:
        raise e


def backup_atlas():
    try:
        # MongoDB Atlas credentials and connection information
        #MONGODB_ATLAS_URI = f"mongodb+srv://{MONGODB_ATLAS_USERNAME}:{MONGODB_ATLAS_PASSWORD}@{MONGODB_ATLAS_CLUSTER}.g93kgy3.mongodb.net/{MONGODB_ATLAS_DB_NAME}"
        # MongoDB Docker container credentials and connection information
        #DOCKER_CONTAINER_URI = f"mongodb://{DOCKER_CONTAINER_USERNAME}:{DOCKER_CONTAINER_PASSWORD}@{DOCKER_CONTAINER_HOST}:{DOCKER_CONTAINER_PORT}/{DOCKER_CONTAINER_DB_NAME}"

        # Get the current timestamp to use in the backup file name
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # Define the backup file name
        #backup_file = f"backup_{timestamp}.gz"

        # Use mongodump to export data from MongoDB Atlas
        subprocess.run(["sh -c mongodump --uri=mongodb+srv://Sp4rda:CuIHqKlU8dFzZ4zt@gns-db.g93kgy3.mongodb.net/gns_mongodb"])

        # Use mongorestore to import the data into the MongoDB Docker container
        #subprocess.run(["mongorestore", "--uri", DOCKER_CONTAINER_URI, "--gzip", "--archive", backup_file])

        print(f"Backup created and restored successfully to the MongoDB Docker container.")
        #print(f"Backup file: {backup_file}")

    except Exception as e:
        print(f"An error occurred during backup and restore: {e}")

