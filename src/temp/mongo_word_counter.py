from pymongo import MongoClient

# Usage example
MONGODB_USERNAME = "Sp4rda"
MONGODB_PASSWORD = "CuIHqKlU8dFzZ4zt"
MONGODB_CLUSTER = "gns-db"
DB_NAME = "gns_mongodb"
COLLECTION_NAME = "articles"
MONGODB_URL = f"mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_CLUSTER}.g93kgy3.mongodb.net/{DB_NAME}?retryWrites=true&w=majority"


def calculate_average_word_count_mongodb():
    try:
        # Connect to MongoDB using the provided URI
        client = MongoClient(MONGODB_URL)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        # Retrieve documents with Translated Title
        documents = collection.find({"Translated Title": {"$exists": True}})

        total_word_count = 0
        total_documents = 0

        for document in documents:
            translated_title = document["Translated Title"]
            words = translated_title.split()
            total_word_count += len(words)
            total_documents += 1

        if total_documents == 0:
            print("No documents with 'Translated Title' found.")
        else:
            average_word_count = total_word_count / total_documents
            print(f"Average word count in 'Translated Title' field: {average_word_count:.2f} words")

        client.close()

    except Exception as e:
        print(f"An error occurred: {e}")

calculate_average_word_count_mongodb()