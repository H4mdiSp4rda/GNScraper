from gevent import monkey
monkey.patch_all(thread=False, select=False)

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
import json  # Import the json module

#import warnings
#warnings.filterwarnings("ignore")
from utils import setup_logging


# Create different loggers for different functions
translate_logger = setup_logging("TranslateLogger", "Scrap")
extract_link_logger = setup_logging("ExtractLinkLogger", "Scrap")
scrap_articles_logger = setup_logging("ScrapArticlesLogger", "Scrap")

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


# Define functions to read from and write to JSON file
def read_json_file(filename):
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        return []

def write_json_file(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)


# Define the scrap_articles function
def scrap_articles(language_code, search_query, insert_method, country, debug_mode=False):
    try:
        # Initialize counters
        successful_scrapes = 0
        total_retries = 0
        total_failures = 0

        language_info = LANGUAGE_CONFIG.get(language_code)
        if language_info:
            gn = GoogleNews(lang=language_info['language'], country=country)

            search_results = gn.search(search_query)
            data = read_json_file('scraped_data.json')  # Read existing data from JSON file

            country_code = country.split()[0]
            first_search_term = search_query.split("OR")[0].strip()
            for entry in tqdm(search_results['entries'][:NUM_ARTICLES_TO_SCRAP], desc=f"Scraping {country_code} ({first_search_term})", mininterval=1.0):
                if debug_mode:
                    print(f"Scraping: Country - {country}, Language - {language_code}, Search Term - {first_search_term}")

                article_link = extract_link(entry['link'])
                published_time = entry['published']

                # Check for duplicate article based on URL and published time
                is_duplicate = any(article.get("Article URL") == article_link and article.get("Published Time") == published_time for article in data)
                if is_duplicate:
                    scrap_articles_logger.info(f"Skipping duplicate article: {article_link}")
                    continue

                retries = 0
                last_exception_message = None
                for retry_count in range(max_retries):
                    try:
                        retry_delay = random.uniform(1, 6)
                        headers = {'User-Agent': user_agent.random, 'Referer': 'https://www.google.com/'}
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
                            successful_scrapes += 1
                            break

                    except Exception as e:
                        retries += 1
                        last_exception_message = str(e)
                        if retry_count < max_retries - 1:
                            time.sleep(retry_delay)

                total_retries += retries
                if retries == max_retries:
                    failure_message = f"FAIL after {max_retries} retries. Last error: {last_exception_message}"
                    scrap_articles_logger.error(failure_message)
                    total_failures += 1
                elif retries > 0:
                    success_message = f"SUCCESS after {retries} retries. Last error: {last_exception_message}"
                    scrap_articles_logger.info(success_message)

                time.sleep(retry_delay)

            # Write data to JSON file
            write_json_file('scraped_data.json', data)

            # Log summary at the end
            scrap_articles_logger.info(f"Scraping Summary for {country} - '{first_search_term}': Successful Iterations - {successful_scrapes}, Total Retries - {total_retries}, Total Failures - {total_failures}")

    except Exception as e:
        scrap_articles_logger.error(f"An error occurred during scraping for {country}: {e}", exc_info=True)
