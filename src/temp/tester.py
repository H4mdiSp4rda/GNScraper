from newspaper import Article, Config
from pygooglenews import GoogleNews
from fake_useragent import UserAgent 

user_agent = UserAgent()

def scrape_article(url, query):
    # Get a random user agent for this request
    current_user_agent = user_agent.random
    print("User Agent:", current_user_agent)  # Print the user agent string

    # Define your custom headers for Newspaper3k
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    # Create a configuration object for Newspaper3k and set the custom headers
    newspaper_config = Config()
    newspaper_config.headers = HEADERS
    newspaper_config.request_timeout = 10

    # Create a GoogleNews object
    gn = GoogleNews()

    # Perform a search with PyGoogleNews
    search_results = gn.search(query)

    # Get the first search result (assumes it's the most relevant)
    first_result = search_results['entries'][0]

    # Extract and print the date and source from PyGoogleNews
    date_of_publish_google = first_result.published
    source_google = first_result.source

    # Create an Article object with Newspaper3k and specify the configuration
    article = Article(url, config=newspaper_config)

    # Download and parse the article with Newspaper3k
    article.download()
    article.parse()

    # Extract the title, date, source, and content
    title = article.title
    date_of_publish_newspaper = article.publish_date
    source_newspaper = article.source_url
    content = article.text

    # Return the results as a dictionary
    results = {
        "Title": title,
        "Source (Google News)": source_google,
        "Date of Publish (Google News)": date_of_publish_google,
        "Content": content
    }

    return results

# Example usage:
url = "https://www.ouest-france.fr/sport/football/equipe-italie/video-pirlo-sur-le-scandale-des-paris-dommage-de-gacher-sa-carriere-et-son-talent-pour-ces-choses-la-052ab362-1656-3a1d-887c-3e71e3543483"
query = "Pirlo sur le scandale des paris : Dommage de gâcher sa carrière et son talent pour ces choses-là"
result = scrape_article(url, query)

# Print the results
for key, value in result.items():
    print(f"{key}:", value)
