import json

# Define the path to the JSON file
JSON_FILE_PATH = 'data.json'

def connect_to_json():
    try:
        with open(JSON_FILE_PATH, 'r') as json_file:
            data = json.load(json_file)
        return data
    except Exception as e:
        print(f"An error occurred while connecting to the JSON file: {e}")
        return None



def is_duplicate(data, article_link, published_time):
    for article in data:
        if article.get("Article URL") == article_link and article.get("Published Time") == published_time:
            return True
    return False


def insert_data_into_json(data, country):
    try:
        with open(JSON_FILE_PATH, 'r+') as json_file:
            existing_data = json.load(json_file)
            json_file.seek(0)  # Move the cursor to the beginning of the file
            for article_data in data:
                if not is_duplicate(existing_data, article_data["Article URL"], article_data["Published Time"]):
                    existing_data.append(article_data)
            json_file.truncate()  # Clear the file content
            json.dump(existing_data, json_file, indent=4)  # Write the updated data
        print(f"Inserted {len(data)} unique documents into the JSON file.")
    except Exception as e:
        print(f"An error occurred while inserting data into the JSON file for {country}: {e}")


def query_json():
    try:
        data = connect_to_json()
        if data:
            for document in data:
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
            print(f"Number of articles found in the JSON file: {len(data)}")
        else:
            print("No articles found in the JSON file.")
    except Exception as e:
        print(f"An error occurred while querying the JSON file: {e}")



keywords = [
    "Ecological transition",
    "Environmental sustainability",
    "Climate change mitigation",
    "Green economy",
    "Carbon neutrality",
    "Renewable energy",
    "Solar power",
    "Wind energy",
    "Hydroelectric power",
    "Geothermal energy",
    "Bioenergy",
    "Energy conservation",
    "Energy efficiency",
    "Energy-saving technology",
    "Low-energy buildings",
    "Smart grid",
    "Electric vehicles",
    "Hybrid vehicles",
    "Public transportation",
    "Cycling infrastructure",
    "Carpooling",
    "Conservation",
    "Biodiversity",
    "Deforestation",
    "Water management",
    "Waste management"
]

