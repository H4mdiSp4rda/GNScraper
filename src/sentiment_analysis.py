from gevent import monkey
monkey.patch_all(thread=False, select=False)

from transformers import BertTokenizer, BertForSequenceClassification, pipeline, AutoTokenizer, AutoModelForSequenceClassification, AutoModelForTokenClassification
from mongo_ops import connect_to_mongo_atlas
import torch
from flair.data import Sentence
from flair.models import SequenceTagger
from tqdm import tqdm
from utils import setup_logging
from datetime import datetime

# Set up logging for sentiment analysis
analyze_sentiment_logger = setup_logging("AnalyzeSentimentLogger", "logs/SA.log")

# Create a logger for classify_SA function
classify_SA_logger = setup_logging("ClassifySALogger", "logs/SA.log")

classify_ESG_logger = setup_logging("ClassifyESGLogger", "logs/ESG.log")
# Create a logger for classify_FLS function
classify_FLS_logger = setup_logging("ClassifyFLSLogger", "logs/FLS.log")
# Create a logger for classify_ESG9 function
classify_ESG9_logger = setup_logging("ClassifyESG9Logger", "logs/ESG9.log")

classify_NER_logger = setup_logging("NERLogger", "logs/NER.log")


# Map numeric labels to English language representations
LABEL_MAPPING = {
    0: "Positive",
    1: "Negative",
    2: "Neutral"
}

def analyze_sentiment(text):
    try:
        # Load FinBERT model and tokenizer
        pipe = pipeline("text-classification", model="ProsusAI/finbert")
        tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
        # Tokenize and convert to tensor
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        outputs = model(**inputs)

        # Get predicted label and logits
        logits = outputs.logits
        predicted_class = torch.argmax(logits, dim=1).item()

        return predicted_class, torch.nn.functional.softmax(logits, dim=1)

    except Exception as e:
        analyze_sentiment_logger.error(f"Error during sentiment analysis: {str(e)}")
        return None, None

def classify_SA():
    classify_SA_logger.info(f'=== Script execution START (Sentiment Analysis) at: {datetime.now()} ===')
    collection = connect_to_mongo_atlas()
    cursor = collection.find()

    sentiment_labels_added = 0  # Initialize count

    total_documents = collection.count_documents({})  # Use count_documents method on the collection

    # Use tqdm to create a progress bar
    for document in tqdm(cursor, desc="Processing Articles", total=total_documents):
        _id = document["_id"]
        translated_summary = document.get("Translated Summary", "")
        sentiment_label, probabilities = analyze_sentiment(translated_summary)

        # Initialize sentiment_label_text outside of the if block
        sentiment_label_text = "Unknown"

        # Add the sentiment label and probabilities to the log with timestamp
        if sentiment_label is not None and probabilities is not None:
            sentiment_label_text = LABEL_MAPPING.get(sentiment_label, "Unknown")
            classify_SA_logger.info(f"Sentiment analysis completed for document {_id}. Sentiment: {sentiment_label_text}")

        # Add the sentiment label to the MongoDB document
        collection.update_one(
            {"_id": _id},
            {"$set": {"Sentiment Label": sentiment_label_text}}
        )

        if sentiment_label is not None:
            sentiment_labels_added += 1
    print(f"SA Classification complete. {sentiment_labels_added} labels added to the collection.")

    classify_SA_logger.info(f'=== Script execution END (Sentiment Analysis) at: {datetime.now()} with {sentiment_labels_added} labels added to the collection. ===')
    return sentiment_labels_added


def classify_ESG():
    classify_ESG_logger.info(f'=== Script execution START (ESG3 Classification) at: {datetime.now()} ===')

    try:
        # Load FinBERT ESG model and tokenizer
        finbert_esg = BertForSequenceClassification.from_pretrained('yiyanghkust/finbert-esg', num_labels=4)
        tokenizer_esg = BertTokenizer.from_pretrained('yiyanghkust/finbert-esg')

        # Create a text classification pipeline using the ESG model and tokenizer
        nlp_esg = pipeline("text-classification", model=finbert_esg, tokenizer=tokenizer_esg)

        # Connect to MongoDB
        collection = connect_to_mongo_atlas()
        cursor = collection.find()

        esg_labels_added = 0  # Initialize count

        total_documents = collection.count_documents({})  # Use count_documents method on the collection

        # Use tqdm to create a progress bar
        for document in tqdm(cursor, desc="Processing Articles", total=total_documents):
            _id = document["_id"]
            translated_summary = document.get("Translated Summary", "")

            # Perform ESG classification on the translated summary
            esg_results = nlp_esg([translated_summary])

            # Extract ESG label and score
            esg_label = esg_results[0].get('label', 'Not-ESG')  # Replace 'None' with 'Not-ESG'
            esg_score = esg_results[0].get('score', 0.0)

            # Replace "None" with "Not ESG Related"
            esg_label = esg_label if esg_label != "None" else "Not ESG Related"

            # Replace the existing TAGS field in the MongoDB document with the new ESG label and score
            collection.update_one(
                {"_id": _id},
                {"$set": {"TAGS": [{"ESG Label": esg_label, "ESG Score": esg_score}]}}
            )

            classify_ESG_logger.info(f"ESG3 classification completed for document {_id}. Label: {esg_label}, Score: {esg_score}")

            esg_labels_added += 1

        print(f"ESG3 Classification complete. {esg_labels_added} labels added to the collection.")
        classify_ESG_logger.info(f'=== Script execution END (ESG3 Classification) at: {datetime.now()} with {esg_labels_added} labels added to the collection ===')

    except Exception as e:
        classify_ESG_logger.error(f"Error during ESG3 classification: {str(e)}")
    return esg_labels_added


def classify_FLS():
    classify_FLS_logger.info(f'=== Script execution START (FLS Classification) at: {datetime.now()} ===')
    try:
        # Load FinBERT-FLS model and tokenizer
        finbert_fls = BertForSequenceClassification.from_pretrained('yiyanghkust/finbert-fls', num_labels=3)
        tokenizer_fls = BertTokenizer.from_pretrained('yiyanghkust/finbert-fls')

        # Create a text classification pipeline using the FinBERT-FLS model and tokenizer
        nlp_fls = pipeline("text-classification", model=finbert_fls, tokenizer=tokenizer_fls)

        # Connect to MongoDB
        collection = connect_to_mongo_atlas()
        cursor = collection.find()

        fls_labels_added = 0  # Initialize count

        total_documents = collection.count_documents({})  # Use count_documents method on the collection

        # Use tqdm to create a progress bar
        for document in tqdm(cursor, desc="Processing Articles", total=total_documents):
            _id = document["_id"]
            translated_summary = document.get("Translated Summary", "")

            # Perform FinBERT-FLS classification on the translated summary
            fls_results = nlp_fls([translated_summary])

            # Extract FinBERT-FLS label and score
            fls_label = fls_results[0].get('label', 'Not-FLS')  # Replace 'None' with 'Not-FLS'
            fls_score = fls_results[0].get('score', 0.0)

            # Replace "None" with "Not FLS Related"
            fls_label = fls_label if fls_label != "None" else "Not FLS Related"

            # Update the existing TAGS field in the MongoDB document with the new FinBERT-FLS label and score
            collection.update_one(
                {"_id": _id},
                {"$addToSet": {"TAGS": {"FLS Label": fls_label, "FLS Score": fls_score}}}
            )

            classify_FLS_logger.info(f"FinBERT-FLS classification completed for document {_id}. Label: {fls_label}, Score: {fls_score}")

            fls_labels_added += 1

        print(f"FinBERT-FLS Classification complete. {fls_labels_added} labels added to the collection.")
        classify_FLS_logger.info(f'=== Script execution END (FLS Classification) at: {datetime.now()} with {fls_labels_added} labels added to the collection ===')

    except Exception as e:
        classify_FLS_logger.error(f"Error during FinBERT-FLS classification: {str(e)}")
    return fls_labels_added


def classify_ESG9():
    try:
        classify_ESG9_logger.info(f'=== Script execution START (ESG9 Classification) at: {datetime.now()} ===')
        # Load FinBERT-ESG model and tokenizer
        finbert_esg = BertForSequenceClassification.from_pretrained('yiyanghkust/finbert-esg-9-categories', num_labels=9)
        tokenizer_esg = BertTokenizer.from_pretrained('yiyanghkust/finbert-esg-9-categories')
        nlp_esg = pipeline("text-classification", model=finbert_esg, tokenizer=tokenizer_esg)

        # Define the ESG label mapping
        ESG_LABEL_MAPPING = {
            0: "Climate Change",
            1: "Human Rights",
            2: "Labor Issues",
            3: "Product Responsibility",
            4: "Public Policy",
            5: "Shareholders and Governance",
            6: "Social Opportunities",
            7: "Water Management",
            8: "Not ESG Related"
        }

        # Connect to MongoDB
        collection = connect_to_mongo_atlas()
        cursor = collection.find()

        esg_labels_added = 0  # Initialize count

        total_documents = collection.count_documents({})  # Use count_documents method on the collection

        # Use tqdm to create a progress bar
        for document in tqdm(cursor, desc="Processing Articles", total=total_documents):
            _id = document["_id"]
            translated_summary = document.get("Translated Summary", "")

            # Perform FinBERT-ESG classification on the translated summary
            esg_results = nlp_esg([translated_summary])

            # Extract ESG label and score
            esg_label = esg_results[0].get('label', 'Not ESG Related')  # Replace 'None' with 'Not ESG Related'
            esg_score = esg_results[0].get('score', 0.0)

            # Skip if the article is "Not ESG Related"
            if esg_label == "Not ESG Related":
                continue

            # Update the existing TAGS field in the MongoDB document with the new ESG label and score
            collection.update_one(
                {"_id": _id},
                {"$addToSet": {"TAGS": {"ESG Label": esg_label, "ESG Score": esg_score}}}
            )

            classify_ESG9_logger.info(f"FinBERT-ESG9 classification completed for document {_id}. Label: {esg_label}, Score: {esg_score}")

            esg_labels_added += 1

        print(f"ESG9 Classification complete. {esg_labels_added} labels added to the collection.")
        classify_ESG9_logger.info(f'=== Script execution END (ESG9 Classification) at: {datetime.now()} with {esg_labels_added} labels added to the collection ===')

    except Exception as e:
        classify_ESG9_logger.error(f"Error during ESG9 classification: {str(e)}")
    return esg_labels_added


def classify_NER():
    classify_NER_logger.info(f'=== Script execution START (NER Classification) at: {datetime.now()} ===')

    try:
        # Load Flair NER model
        tagger = SequenceTagger.load("flair/ner-english-ontonotes-large")

        # Connect to MongoDB
        collection = connect_to_mongo_atlas()
        cursor = collection.find()

        ner_entities_added = 0  # Initialize count

        total_documents = collection.count_documents({})  # Use count_documents method on the collection

        # Use tqdm to create a progress bar
        for document in tqdm(cursor, desc="Processing Articles", total=total_documents):
            _id = document["_id"]
            translated_summary = document.get("Translated Summary", "")

            # Make sentence
            sentence = Sentence(translated_summary)

            # Predict NER tags
            tagger.predict(sentence)

            # Extract recognized entities
            entities = [entity.tag for entity in sentence.get_spans('ner')]

            # Filter entities to include only ORG and GPE
            filtered_entities = [entity for entity in entities if entity in ["ORG", "GPE"]]

            # Update the MongoDB document, overwriting the existing "Entities" field
            collection.update_one(
                {"_id": _id},
                {"$set": {"Entities": filtered_entities}}
            )

            classify_NER_logger.info(f"NER classification completed for document {_id}. Entities added: {filtered_entities}")

            ner_entities_added += len(filtered_entities)

        print(f"NER Classification complete. {ner_entities_added} entities added to the collection.")
        classify_NER_logger.info(f'=== Script execution END (NER Classification) at: {datetime.now()} with {ner_entities_added} entities added to the collection ===')

    except Exception as e:
        classify_NER_logger.error(f"Error during NER classification: {str(e)}")

    return ner_entities_added