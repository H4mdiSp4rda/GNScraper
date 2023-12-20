from gevent import monkey
monkey.patch_all(thread=False, select=False)

from mongo_ops import insert_data_into_mongodb, is_duplicate, connect_to_mongo_atlas
from lang_dict import LANGUAGE_CONFIG
from newspaper import Article, Config
from pygooglenews import GoogleNews
from bs4 import BeautifulSoup
import requests
from tqdm import tqdm
from urllib3.exceptions import NewConnectionError
from newspaper.article import ArticleException
import random
import time
from fake_useragent import UserAgent
import translators as ts
import grequests

#import warnings
#warnings.filterwarnings("ignore")
from utils import setup_logging


# Create different loggers for different functions
translate_logger = setup_logging("TranslateLogger", "logs/Scrap.log")
extract_link_logger = setup_logging("ExtractLinkLogger", "logs/Scrap.log")
scrap_articles_logger = setup_logging("ScrapArticlesLogger", "logs/Scrap.log")



# Constants
NUM_ARTICLES_TO_SCRAP = 5
max_retries = 3
user_agent = UserAgent()

# Define the LANGUAGE_CONFIG dictionary
# LANGUAGE_CONFIG is on gitignore due to confidentiality reasons




def translate_to_english(original_text):
    try:
        translated_text = ts.translate_text(original_text, translator='google', from_language='auto', to_language='en')
        return translated_text
    except Exception as e:
        error_message = f"Translation error: {e.__class__.__name__} - {str(e)}"
        translate_logger.error(error_message)
        return original_text

def extract_link(url):
    user_agent = UserAgent().random
    headers = {'User-Agent': user_agent}

    try:
        # Create a list of grequests to make asynchronous requests
        requests = [grequests.get(url, headers=headers)]

        # Send the requests asynchronously
        responses = grequests.map(requests)

        if responses and responses[0].status_code == 200:
            response = responses[0]
            soup = BeautifulSoup(response.content, 'html.parser')
            try:
                link = soup.find('a', jsname='tljFtd')['href']
                return link
            except TypeError:
                extract_link_logger.error(f"Error extracting link from {url}")  # Log the error
                return None
        else:
            extract_link_logger.error(f"Response returned status code {responses[0].status_code}")  # Log the error
            sleep_time = random.randint(1, 6)
            extract_link_logger.info(f"Sleeping for {sleep_time} seconds...")  # Log info
            time.sleep(sleep_time)
            return extract_link(url)

    except Exception as e:
        extract_link_logger.error(f"An error occurred while processing '{url}': {e}")  # Log the error
        return None


# Define the scrap_articles function
def scrap_articles(language_code, search_query, insert_method, country, debug_mode=False):
    try:
        # Assuming LANGUAGE_CONFIG and other necessary configurations are defined
        language_info = LANGUAGE_CONFIG.get(language_code)
        if language_info:
            gn = GoogleNews(lang=language_info['language'], country=country)

            search_results = gn.search(search_query)
            data = []

            # Extract the country code from the country variable
            country_code = country.split()[0]

            for entry in tqdm(search_results['entries'][:NUM_ARTICLES_TO_SCRAP], desc=f"Scraping {country_code} ({search_query.split()[0]})", mininterval=1.0):
                if debug_mode:
                    print(f"Scraping: Country - {country}, Language - {language_code}, Search Term - {search_query.split()[0]}")

                article_link = extract_link(entry['link'])
                published_time = entry['published']

                collection = connect_to_mongo_atlas()

                if is_duplicate(collection, article_link, published_time):
                    scrap_articles_logger.info(f"Skipping duplicate article: {article_link}")
                    continue

                for retry_count in range(max_retries):
                    try:
                        retry_delay = random.uniform(1, 6)
                        headers = {
                            'User-Agent': user_agent.random,
                            'Referer': 'https://www.google.com/',
                        }
                        config = Config()
                        config.headers = headers
                        config.request_timeout = retry_delay

                        article = Article(article_link, config=config)
                        article.download()
                        article.parse()
                        article.nlp()

                        if article.is_parsed:
                            translated_title = translate_to_english(article.title)
                            translated_summary = translate_to_english(article.summary)
                            data.append({
                                "Title": article.title,
                                "Translated Title": translated_title,
                                "Source": entry.get('source', ''),
                                "Published Time": entry['published'],
                                "Article URL": article_link,
                                "Content": article.text,
                                "Article Summary": article.summary,
                                "Translated Summary": translated_summary,
                                "Language": language_code,
                                "Country": country
                            })
                            break

                    except requests.exceptions.HTTPError as e:
                        scrap_articles_logger.error(f"HTTPError ({e.response.status_code} {e.response.reason}): {e}")
                        if e.response.status_code == 403:
                            time.sleep(retry_delay)
                    except ConnectionError as e:
                        scrap_articles_logger.error(f"ConnectionError: {e}")
                    except Exception as e:
                        scrap_articles_logger.error(f"An error occurred while processing '{article_link}': {e}")

                    if retry_count < max_retries - 1:
                        scrap_articles_logger.info(f"Retrying the request in {retry_delay} seconds...")
                        time.sleep(retry_delay)

                time.sleep(retry_delay)

            if insert_method == "auto":
                insert_data_into_mongodb(data, country)
            else:
                insert_option = input("Do you want to store the scraped data in the database? (yes/no): ").strip().lower()
                if insert_option == "yes":
                    insert_data_into_mongodb(data, country)

    except Exception as e:
        scrap_articles_logger.error(f"An error occurred during scraping for {country}: {e}", exc_info=True)
