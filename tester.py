import argparse
from newspaper import Article
from pygooglenews import GoogleNews
import pymongo
from tqdm import tqdm

# Constants
NUM_ARTICLES_TO_SCRAP = 20
MONGODB_URL = "mongodb://172.17.0.2:27017/"
DB_NAME = "gns_raw"
COLLECTION_NAME = "articles"

# Define the supported regions and their Google News country codes for each language
SUPPORTED_LANGUAGES = {
    'FR': ['CM', 'CI', 'BJ', 'SN', 'GN'],
    'AR': ['EG', 'AE', 'OM', 'TN', 'MA'],
    'ES': ['MX', 'CO', 'PE', 'AR', 'GT'],
    'PT': ['BR', 'AO', 'MZ', 'GW', 'CV'],
    'RU': ['RU', 'BY', 'UZ', 'KZ', 'UA'],
}

# Define the list of themes with their associated search queries for each language
SEARCH_THEMES = {
    'Compliance Risk': [
        'scandale financier',
        'fraude financière',
        'procès financier',
        'tribunal financier',
        'appel financier',
        'accusé de scandale financier',
        # ... (other queries in the language related to compliance risk)
    ],
    'Credit Risk / Rating': [
        'risque de crédit',
        'notation financière',
        'défaut financier',
        'insolvabilité financière',
        'suspension financière',
        # ... (other queries in the language related to credit risk/rating)
    ],
    'ESG': [
        'ESG',
        'durabilité',
        'finance verte',
        'prêts verts',
        # ... (other queries in the language related to ESG)
    ],
    'Opportunity': [
        'investissement financier',
        'financement financier',
        'accord financier',
        # ... (other queries in the language related to opportunity)
    ],
}

SEARCH_THEMES_AR = {
    'Compliance Risk': [
        'فضيحة مالية',
        'احتيال مالي',
        'محكمة مالية',
        'استئناف مالي',
        'اتهم بفضيحة مالية',
        # ... (other queries in Arabic related to compliance risk)
    ],
    'Credit Risk / Rating': [
        'مخاطر الائتمان',
        'تقييم مالي',
        'افلاس مالي',
        'عدم السداد المالي',
        'تعليق مالي',
        # ... (other queries in Arabic related to credit risk/rating)
    ],
    'ESG': [
        'ESG',
        'استدامة',
        'تمويل أخضر',
        'قروض خضراء',
        # ... (other queries in Arabic related to ESG)
    ],
    'Opportunity': [
        'استثمار مالي',
        'تمويل مالي',
        'اتفاق مالي',
        # ... (other queries in Arabic related to opportunity)
    ],
}
SEARCH_THEMES_ES = {
    'Compliance Risk': [
        'escándalo financiero',
        'fraude financiero',
        'juicio financiero',
        'apelación financiera',
        'acusado de escándalo financiero',
        # ... (other queries in Spanish related to compliance risk)
    ],
    'Credit Risk / Rating': [
        'riesgo crediticio',
        'calificación financiera',
        'incumplimiento financiero',
        'insolvencia financiera',
        'suspensión financiera',
        # ... (other queries in Spanish related to credit risk/rating)
    ],
    'ESG': [
        'ESG',
        'sostenibilidad',
        'financiamiento verde',
        'préstamos verdes',
        # ... (other queries in Spanish related to ESG)
    ],
    'Opportunity': [
        'inversión financiera',
        'financiamiento financiero',
        'acuerdo financiero',
        # ... (other queries in Spanish related to opportunity)
    ],
}

SEARCH_THEMES_PT = {
    'Compliance Risk': [
        'escândalo financeiro',
        'fraude financeira',
        'processo financeiro',
        'recurso financeiro',
        'acusado de escândalo financeiro',
        # ... (other queries in Portuguese related to compliance risk)
    ],
    'Credit Risk / Rating': [
        'risco de crédito',
        'classificação financeira',
        'incumprimento financeiro',
        'insolvência financeira',
        'suspensão financeira',
        # ... (other queries in Portuguese related to credit risk/rating)
    ],
    'ESG': [
        'ESG',
        'sustentabilidade',
        'financiamento verde',
        'empréstimos verdes',
        # ... (other queries in Portuguese related to ESG)
    ],
    'Opportunity': [
        'investimento financeiro',
        'financiamento financeiro',
        'acordo financeiro',
        # ... (other queries in Portuguese related to opportunity)
    ],
}

SEARCH_THEMES_RU = {
    'Compliance Risk': [
        'финансовый скандал',
        'финансовое мошенничество',
        'финансовое судебное разбирательство',
        'финансовая аппеляция',
        'обвинен в финансовом скандале',
        # ... (other queries in Russian related to compliance risk)
    ],
    'Credit Risk / Rating': [
        'кредитный риск',
        'финансовое рейтингование',
        'дефолт по финансам',
        'финансовая несостоятельность',
        'финансовая приостановка',
        # ... (other queries in Russian related to credit risk/rating)
    ],
    'ESG': [
        'ESG',
        'устойчивость',
        'зеленое финансирование',
        'зеленые кредиты',
        # ... (other queries in Russian related to ESG)
    ],
    'Opportunity': [
        'финансовые инвестиции',
        'финансовое финансирование',
        'финансовое соглашение',
        # ... (other queries in Russian related to opportunity)
    ],
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
def scrap_articles(language_code, regions, themes):
    try:
        gn = GoogleNews(lang=language_code, country=','.join(regions))

        data = []

        for theme, search_queries in themes.items():
            for query in search_queries:
                search_results = gn.search(query)

                # Create a tqdm progress bar for the articles
                progress_bar = tqdm(search_results['entries'][:NUM_ARTICLES_TO_SCRAP], desc=f'Scraping {theme}')

                for entry in progress_bar:
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
                            "Language": language_code
                        })
                    except Exception as e:
                        # Handle errors by printing a message and continue scraping
                        print(f"Error scraping an article: {e}")
                        continue

        return data
    except Exception as e:
        print(f"An error occurred during scraping: {e}")

# ... (insert_data_into_mongodb, query_mongodb, and main functions remain unchanged)
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
            print("Content:")
            print(document.get("Content")) #uncomment if  u wanna check article text scraped
            print("\n" + "=" * 50 + "\n") ##uncomment if  u wanna check article text scraped

        if count == 0:
            print("No articles found in the MongoDB collection.")
        else:
            print(f"Number of articles found in the MongoDB collection: {count}")

    except Exception as e:
        print(f"An error occurred while querying the database: {e}")

def main():
    parser = argparse.ArgumentParser(description="Scrape and manage data in MongoDB")
    parser.add_argument("--language", choices=SUPPORTED_LANGUAGES.keys(), required=True, help="Select the language for scraping")
    args = parser.parse_args()

    language = args.language
    regions = SUPPORTED_LANGUAGES.get(language)
    language_code = language[:2]  # Get the first two characters of the language name as the language code

    if regions:
        # Get the themes and language-specific queries for the selected language
        themes = SEARCH_THEMES.get(language, {})  # Default to an empty dictionary if themes are not defined for the language

        scraped_data = scrap_articles(language_code, regions, themes)

        if scraped_data:
            print(f"Scraped {len(scraped_data)} articles in {language_code} for the selected themes.")
            insert_option = input("Do you want to store the scraped data in the database? (yes/no): ").strip().lower()
            if insert_option == "yes":
                insert_data_into_mongodb(scraped_data)
            else:
                print("Scraped data not stored in the database.")
    else:
        print("Selected language is not supported.")

if __name__ == "__main__":
    main()
