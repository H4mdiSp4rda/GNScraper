import csv
import requests
from newspaper import Article
import pygooglenews

# Initialize Google News client
gn = pygooglenews.GoogleNews()

# Define your search query and get search results
search_query = "banking industry partnership news"
search_results = gn.search(search_query)

# Create a list to store the extracted data
data = []

# Function to download an article, handle errors, and return article data
def download_article(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        article = Article(url)
        article.set_html(response.text)
        article.parse()
        return article.title, article.text
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error ({e.response.status_code}): {e.response.reason}")
    except Exception as e:
        print(f"An error occurred while processing an article: {e}")
    return None, None

# Iterate through the search results and scrape article content
for entry in search_results['entries']:
    article_url = entry['link']
    title, content = download_article(article_url)
    if title and content:
        source = entry['source']
        published_time = entry['published']
        # Append the data to the list
        data.append([title, source, published_time, article_url, content])

# Save the data to a CSV file
with open('raw_scraped_data.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    # Write header row
    writer.writerow(['Title', 'Source', 'Published Time', 'Article URL', 'Content'])
    # Write data rows
    writer.writerows(data)

# Print or store the extracted data as needed
