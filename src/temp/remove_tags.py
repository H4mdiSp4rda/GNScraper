import pymongo

MONGODB_ATLAS_USERNAME = "Sp4rda"
MONGODB_ATLAS_PASSWORD = "CuIHqKlU8dFzZ4zt"
MONGODB_ATLAS_CLUSTER = "gns-db"
MONGODB_ATLAS_DB_NAME = "gns_mongodb"
MONGODB_ATLAS_URI = f"mongodb+srv://{MONGODB_ATLAS_USERNAME}:{MONGODB_ATLAS_PASSWORD}@{MONGODB_ATLAS_CLUSTER}.g93kgy3.mongodb.net/{MONGODB_ATLAS_DB_NAME}?retryWrites=true&w=majority"
COLLECTION_NAME = "articles"

def connect_to_mongo_atlas():
    try:
        client = pymongo.MongoClient(MONGODB_ATLAS_URI)
        db = client[MONGODB_ATLAS_DB_NAME]
        collection = db[COLLECTION_NAME]
        return collection
    except Exception as e:
        print(f"An error occurred while connecting to MongoDB Atlas: {e}")
        return None

def remove_tags_field(collection):
    try:
        # Use $unset to remove the "tags" field from all documents
        collection.update_many({}, {"$unset": {"tags": ""}})
        print("Field 'tags' removed from all documents.")
    except Exception as e:
        print(f"An error occurred while removing the 'tags' field: {e}")

# Example usage:
if __name__ == "__main__":
    articles_collection = connect_to_mongo_atlas()

    if articles_collection:
        remove_tags_field(articles_collection)
