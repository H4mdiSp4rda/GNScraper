from gevent import monkey
from regex import F
monkey.patch_all(thread=False, select=False)

import argparse
import sys
from pygooglenews import GoogleNews
from mongo_ops import purge_db, query_mongodb, backup_atlas
from RF_classify import classify_RF
from sentiment_analysis import classify_ESG, classify_SA, classify_FLS, classify_ESG9, classify_NER
from lang_dict import LANGUAGE_CONFIG
from scrap import scrap_articles
from RF_classify import classify_RF
from utils import setup_logging
from datetime import datetime

# Create a logger for main function
main_logger = setup_logging("MainLogger", "Scrap")


# Define the main function
def main():
    parser = argparse.ArgumentParser(description="Scrape news articles, manage data, and store it in MongoDB.")

    # Add arguments
    parser.add_argument("--purge", action="store_true", help="Clear all documents from the MongoDB collection.")
    parser.add_argument("--scrap", nargs=2, metavar=('LANGUAGE', 'INSERT_METHOD'),
                        help="Scrape news articles for a specific language and specify the insertion method. "
                             "Example: --scrap FR auto or --scrap AR auto.")
    parser.add_argument("--query", action="store_true", help="Query and display documents in the MongoDB collection.")
    parser.add_argument("--classify", metavar="CLASSIFICATION", help="F/R to classify news articles as real or fake, SA for Sentiment Analysis, ESG for ESG classification.")
    parser.add_argument("--backup", action="store_true", help="Create a backup of MongoDB Atlas and restore it in a Docker container.")

    # Add the --help option as a default action
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    scraped_data = None  # Initialize scraped_data

    if args.purge:
        purge_db()
        # Exit after purging without adding any messages
        sys.exit(0)

    if args.query:
        query_mongodb()
        # Exit after querying without adding any messages
        sys.exit(0)

    if args.backup:
        # Call the backup function here
        backup_atlas()
        sys.exit(0)

    if args.classify:
        classification_type = args.classify
        if classification_type in ["R/F", "ESG", "SA", "FLS", "ESG9", "NER"]:  
            if classification_type == "R/F":
                classify_RF()
            elif classification_type == "ESG":
                classify_ESG()
            elif classification_type == "SA":
                classify_SA()
            elif classification_type == "FLS":  
                classify_FLS()
            elif classification_type == "ESG9":  
                classify_ESG9()
            elif classification_type == "NER":
                classify_NER()

        else:
            print("Error: The sub-argument for --classify must be 'R/F', 'ESG', ESG9,'SA', or 'FLS'.")
            sys.exit(1)

    if args.scrap:
        main_logger.info(f'=== Script execution START (Scraping) at: {datetime.now()} ===')
        language, insert_method = args.scrap
        language = language.lower() 
        if insert_method not in ["auto", "manual"]:
            print("Error: The insert_method must be 'auto' or 'manual'.")
            sys.exit(1)

        language_config = LANGUAGE_CONFIG.get(language)

        if language_config:
            countries = language_config["countries"]
            gn = GoogleNews(lang=language_config['language'], country=countries[0])

            for country in countries:
                for search_term in language_config["search_terms"]:
                    search_query = f"{search_term} {country}"
                    scraped_data = scrap_articles(language, search_query, insert_method, country)

                    if scraped_data:
                        print(f"Scraped {len(scraped_data)} articles in {language} for search term '{search_term}' and country '{country}'.")
        main_logger.info(f'=== Script Execution End (Scraping) at: {datetime.now()} ===')


if __name__ == "__main__":
    main()
