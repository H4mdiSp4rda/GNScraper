import nltk

def download_nltk_resources():
    nltk_resources = ['punkt', 'stopwords']  # Add any other NLTK resources you need
    for resource in nltk_resources:
        nltk.download(resource)

if __name__ == "__main__":
    download_nltk_resources()
