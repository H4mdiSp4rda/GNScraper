from gevent import monkey
monkey.patch_all(thread=False, select=False)

from mongo_ops import insert_data_into_mongodb, is_duplicate, connect_to_mongo_atlas
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
translate_logger = setup_logging("TranslateLogger", "logs/scrap.log")
extract_link_logger = setup_logging("ExtractLinkLogger", "logs/scrap.log")
scrap_articles_logger = setup_logging("ScrapArticlesLogger", "logs/scrap.log")



# Constants
NUM_ARTICLES_TO_SCRAP = 2
max_retries = 3
retry_delay = 5
user_agent = UserAgent()


# Define the LANGUAGE_CONFIG dictionary
# Constants
NUM_ARTICLES_TO_SCRAP = 3
max_retries = 3
retry_delay = 5
user_agent = UserAgent()


# Define the LANGUAGE_CONFIG dictionary
LANGUAGE_CONFIG = {
    'fr': {
        "search_terms": [
            "scandale financier OR scandale d'entreprise OR scandale bancaire",
            "fraude financière OR fraude bancaire OR fraude d'entreprise",
            "procès financier OR procès bancaire OR procès d'entreprise",
            "tribunal financier OR tribunal bancaire OR tribunal d'entreprise",
            "allégation financière OR allégation bancaire OR allégation d'entreprise",
            "accusation financière OR accusation bancaire OR accusation d'entreprise",
            "amende financière OR amende bancaire OR amende d'entreprise",
            "corruption financière OR corruption bancaire OR corruption d'entreprise",
            "cyberattaque financière OR piratage bancaire OR violation de données d'entreprise",
            "mauvaise conduite financière OR mauvaise conduite bancaire OR mauvaise conduite d'entreprise",
            "violation de sanctions financières OR violation de sanctions bancaires OR violation de sanctions d'entreprise",
            "Panama Papers",
            "Pandora Papers",
            "Paradise Papers",
            "Luanda Leaks",
            "blanchiment d'argent"
        ],
        "countries": ["FR", "SN"],
        "language": "fr",
    },
    'ar': {
        "search_terms": [
            "فضيحة مالية OR فضيحة شركات OR فضيحة بنوك",
            "احتيال مالي OR احتيال بنوك OR احتيال شركات",
            "محكمة مالية OR محكمة بنوك OR محكمة شركات",
            "محكمة مالية OR محكمة بنوك OR محكمة شركات",
            "اتهام مالي OR اتهام بنوك OR اتهام شركات",
            "اتهام مالي OR اتهام بنوك OR اتهام شركات",
            "غرامة مالية OR غرامة بنوك OR غرامة شركات",
            "فساد مالي OR فساد بنوك OR فساد شركات",
            "هجوم مالي إلكتروني OR اختراق بنوك OR انتهاك بيانات شركات",
            "سوء سلوك مالي OR سوء سلوك بنوك OR سوء سلوك شركات",
            "انتهاك عقوبات مالية OR انتهاك عقوبات بنوك OR انتهاك عقوبات شركات",
            "أوراق بنما",
            "أوراق باندورا",
            "أوراق الجنة",
            "تسربات لواندا",
            "غسيل الأموال"
        ],
        "countries": ["EG", "AE"],
        "language": "ar",
    },
    'es': {
        "search_terms": [
            "escándalo financiero OR escándalo bancario OR escándalo corporativo",
            "fraude financiero OR fraude bancario OR fraude corporativo",
            "juicio financiero OR juicio bancario OR juicio corporativo",
            "tribunal financiero OR tribunal bancario OR tribunal corporativo",
            "alegación financiera OR alegación bancaria OR alegación corporativa",
            "acusación financiera OR acusación bancaria OR acusación corporativa",
            "multa financiera OR multa bancaria OR multa corporativa",
            "corrupción financiera OR corrupción bancaria OR corrupción corporativa",
            "ciberataque financiero OR piratería bancaria OR violación de datos corporativos",
            "mala conducta financiera OR mala conducta bancaria OR mala conducta corporativa",
            "violación de sanciones financieras OR violación de sanciones bancarias OR violación de sanciones corporativas",
            "papeles de Panamá",
            "papeles de Pandora",
            "papeles del paraíso",
            "filtraciones de Luanda",
            "lavado de dinero"
        ],
        "countries": ["MX", "CO", "PE", "AR"],
        "language": "es",
    },
    'pt': {
        "search_terms": [
            "escândalo financeiro OR escândalo bancário OR escândalo corporativo",
            "fraude financeira OR fraude bancária OR fraude corporativa",
            "julgamento financeiro OR julgamento bancário OR julgamento corporativo",
            "tribunal financeiro OR tribunal bancário OR tribunal corporativo",
            "alegação financeira OR alegação bancária OR alegação corporativa",
            "acusação financeira OR acusação bancária OR acusação corporativa",
            "multa financeira OR multa bancária OR multa corporativa",
            "corrupção financeira OR corrupção bancária OR corrupção corporativa",
            "ciberataque financeiro OR pirataria bancária OR violação de dados corporativos",
            "má conduta financeira OR má conduta bancária OR má conduta corporativa",
            "violação de sanções financeiras OR violação de sanções bancárias OR violação de sanções corporativas",
            "Panama Papers",
            "Pandora Papers",
            "Papéis do Paraíso",
            "vazamentos de Luanda",
            "lavagem de dinheiro"
        ],
        "countries": ["BR"],
        "language": "pt",
    },
    'ru': {
        "search_terms": [
            "финансовый скандал OR банковский скандал OR корпоративный скандал",
            "финансовое мошенничество OR банковское мошенничество OR корпоративное мошенничество",
            "финансовое судебное разбирательство OR банковское судебное разбирательство OR корпоративное судебное разбирательство",
            "финансовый суд OR банковский суд OR корпоративный суд",
            "финансовые обвинения OR банковские обвинения OR корпоративные обвинения",
            "финансовое обвинение OR банковское обвинение OR корпоративное обвинение",
            "финансовый штраф OR банковский штраф OR корпоративный штраф",
            "финансовое коррупция OR банковская коррупция OR корпоративная коррупция",
            "финансовая кибератака OR банковская кибератака OR нарушение корпоративных данных",
            "финансовое неправильное поведение OR банковское неправильное поведение OR корпоративное неправильное поведение",
            "нарушение финансовых санкций OR нарушение банковских санкций OR нарушение корпоративных санкций",
            "Панамские документы",
            "Пандора Паперс",
            "Документы о рае",
            "Протечки Луанды",
            "отмывание денег"
        ],
        "countries": ["RU", "UA"],
        "language": "ru",
    },
}


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
        language_info = LANGUAGE_CONFIG.get(language_code)
        if language_info:
            gn = GoogleNews(lang=language_info['language'], country=country)

            search_results = gn.search(search_query)
            data = []

            # Extract the country code from the country variable
            country_code = country.split()[0]

            for entry in tqdm(search_results['entries'][:NUM_ARTICLES_TO_SCRAP], desc=f"Scraping {country_code} ({search_query.split()[0]})", mininterval=1.0):
                if debug_mode:
                    # Print the country, language, and search term being scraped
                    print(f"Scraping: Country - {country}, Language - {language_code}, Search Term - {search_query.split()[0]}")

                article_link = extract_link(entry['link'])
                published_time = entry['published']

                # Use connect_to_mongodb to create the collection
                collection = connect_to_mongo_atlas()

                # Check if the article is a duplicate
                if is_duplicate(collection, article_link, published_time):
                    scrap_articles_logger.info(f"Skipping duplicate article: {article_link}")
                    continue  # Move to the next article

                for retry_count in range(max_retries):
                    try:
                        headers = {
                            'User-Agent': user_agent.random,  # Set the User-Agent header
                            'Referer': 'https://www.google.com/',
                            # Add other headers if needed
                        }
                        config = Config()
                        config.headers = headers
                        config.request_timeout = 6

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
                            break  # Successful request, exit the retry loop
                        else:
                            scrap_articles_logger.warning(f"Failed to parse the article '{article_link}'.")
                    except requests.exceptions.HTTPError as e:
                        scrap_articles_logger.error(f"HTTPError ({e.response.status_code} {e.response.reason}): {e}")
                    except ConnectionError as e:
                        scrap_articles_logger.error(f"ConnectionError: {e}")
                        if retry_count < max_retries - 1:
                            scrap_articles_logger.info(f"Retrying the request in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                        else:
                            scrap_articles_logger.error("Max retries reached. Skipping the article.")
                            break  # Max retries reached, exit the retry loop
                    except Exception as e:
                        scrap_articles_logger.error(f"An error occurred while processing '{article_link}': {e}")
                time.sleep(random.uniform(1, 6))

            if insert_method == "auto":
                insert_data_into_mongodb(data, country)
            else:
                insert_option = input("Do you want to store the scraped data in the database? (yes/no): ").strip().lower()
                if insert_option == "yes":
                    insert_data_into_mongodb(data, country)

    except Exception as e:
        scrap_articles_logger.error(f"An error occurred during scraping for {country}: {e}", exc_info=True)
