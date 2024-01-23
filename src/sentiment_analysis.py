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
import pymongo

# Set up logging for sentiment analysis
analyze_sentiment_logger = setup_logging("AnalyzeSentimentLogger", "SA")

# Create a logger for classify_SA function
classify_SA_logger = setup_logging("ClassifySALogger", "SA")

classify_ESG_logger = setup_logging("ClassifyESGLogger", "ESG")
# Create a logger for classify_FLS function
classify_FLS_logger = setup_logging("ClassifyFLSLogger", "FLS")
# Create a logger for classify_ESG9 function
classify_ESG9_logger = setup_logging("ClassifyESG9Logger", "ESG9")

classify_NER_logger = setup_logging("NERLogger", "NER")


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

def classify_SA(skip_existing=False):
    classify_SA_logger.info(f'=== Script execution START (Sentiment Analysis) at: {datetime.now()} ===')
    collection = connect_to_mongo_atlas()

    last_processed_id = None  # Variable to keep track of the last processed document ID
    sentiment_labels_added = 0  # Initialize count
    total_documents = collection.count_documents({})  # Use count_documents method on the collection

    while True:
        try:
            # If the cursor was lost, start from the next document
            if last_processed_id:
                cursor = collection.find({"_id": {"$gt": last_processed_id}})
            else:
                cursor = collection.find()

            for document in tqdm(cursor, desc="Processing Articles", total=total_documents):
                _id = document["_id"]
                last_processed_id = _id  # Update the last processed document ID

                # Skip if skip_existing is True and sentiment label already exists
                if skip_existing and 'Sentiment Label' in document:
                    continue

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

            # Break the loop if all documents have been processed
            break

        except pymongo.errors.CursorNotFound:
            classify_SA_logger.error("Cursor lost. Restarting from last processed document ID.")
            continue  # This continues the while loop, recreating the cursor

    print(f"SA Classification complete. {sentiment_labels_added} labels added to the collection.")
    classify_SA_logger.info(f'=== Script execution END (Sentiment Analysis) at: {datetime.now()} with {sentiment_labels_added} labels added to the collection. ===')
    return sentiment_labels_added


def classify_ESG(skip_existing=False):
    classify_ESG_logger.info(f'=== Script execution START (ESG3 Classification) at: {datetime.now()} ===')

    last_processed_id = None  # Keep track of the last processed document ID
    esg_labels_added = 0  # Initialize count

    try:
        # Load FinBERT ESG model and tokenizer outside the loop
        finbert_esg = BertForSequenceClassification.from_pretrained('yiyanghkust/finbert-esg', num_labels=4)
        tokenizer_esg = BertTokenizer.from_pretrained('yiyanghkust/finbert-esg')
        nlp_esg = pipeline("text-classification", model=finbert_esg, tokenizer=tokenizer_esg)

        # Connect to MongoDB
        collection = connect_to_mongo_atlas()
        total_documents = collection.count_documents({})  # Use count_documents method on the collection

        while True:
            try:
                # If the cursor was lost, start from the next document
                if last_processed_id:
                    cursor = collection.find({"_id": {"$gt": last_processed_id}})
                else:
                    cursor = collection.find()

                for document in tqdm(cursor, desc="Processing Articles", total=total_documents):
                    _id = document["_id"]
                    last_processed_id = _id  # Update the last processed document ID

                    # Skip if skip_existing is True and ESG label already exists
                    if skip_existing and 'ESG' in document:
                        continue

                    translated_summary = document.get("Translated Summary", "")
                    esg_labels = []  # List to store labels for each segment

                    # Process each segment independently
                    max_token_limit = finbert_esg.config.max_position_embeddings
                    tokens = tokenizer_esg.encode(translated_summary, max_length=max_token_limit-2, truncation=True)

                    for i in range(0, len(tokens), max_token_limit):
                        segment = tokens[i:i + max_token_limit]

                        segment_input_ids = segment[:max_token_limit]
                        attention_mask = [1] * len(segment_input_ids) + [0] * (max_token_limit - len(segment_input_ids))
                        attention_mask = attention_mask[:max_token_limit]

                        segment_input_ids = torch.tensor([segment_input_ids])
                        attention_mask = torch.tensor([attention_mask])

                        segmented_summary = tokenizer_esg.decode(segment_input_ids.squeeze().tolist())

                        esg_label = nlp_esg(segmented_summary)[0]['label']
                        esg_label = esg_label if esg_label != "None" else "Not ESG Related"

                        esg_labels.append(esg_label)

                    # Decide the overall label based on individual segment labels
                    overall_esg_label = max(set(esg_labels), key=esg_labels.count)

                    # Update the ESG field in the document
                    collection.update_one({"_id": _id}, {"$set": {"ESG": overall_esg_label}}, upsert=True)

                    esg_labels_added += 1
                    classify_ESG_logger.info(f"ESG3 classification completed for document {_id}. Label: {overall_esg_label}")

                # Break the loop if all documents have been processed
                break

            except pymongo.errors.CursorNotFound:
                classify_ESG_logger.error("Cursor lost. Restarting from last processed document ID.")
                continue  # This continues the while loop, recreating the cursor

        print(f"ESG3 Classification complete. {esg_labels_added} labels added to the collection.")
        classify_ESG_logger.info(f'=== Script execution END (ESG3 Classification) at: {datetime.now()} with {esg_labels_added} labels added to the collection ===')

    except Exception as e:
        classify_ESG_logger.error(f"Error during ESG3 classification: {str(e)}")

    return esg_labels_added

def classify_ESG9(skip_existing=False):
    classify_ESG9_logger.info(f'=== Script execution START (ESG9 Classification) at: {datetime.now()} ===')

    last_processed_id = None  # Keep track of the last processed document ID
    esg_labels_added = 0  # Initialize count

    try:
        # Load FinBERT-ESG model and tokenizer
        finbert_esg = BertForSequenceClassification.from_pretrained('yiyanghkust/finbert-esg-9-categories', num_labels=9)
        tokenizer_esg = BertTokenizer.from_pretrained('yiyanghkust/finbert-esg-9-categories')
        nlp_esg = pipeline("text-classification", model=finbert_esg, tokenizer=tokenizer_esg)

        # Connect to MongoDB
        collection = connect_to_mongo_atlas()
        total_documents = collection.count_documents({})  # Use count_documents method on the collection

        while True:
            try:
                # If the cursor was lost, start from the next document
                if last_processed_id:
                    cursor = collection.find({"_id": {"$gt": last_processed_id}})
                else:
                    cursor = collection.find()

                for document in tqdm(cursor, desc="Processing Articles", total=total_documents):
                    _id = document["_id"]
                    last_processed_id = _id  # Update the last processed document ID

                    # Skip if skip_existing is True and ESG9 label already exists
                    if skip_existing and 'ESG9' in document:
                        continue

                    translated_summary = document.get("Translated Summary", "")
                    esg_field = document.get("ESG", "")

                    # Skip if the article is already marked as "Not ESG Related"
                    if "Not ESG Related" in esg_field:
                        continue

                    # Check if summary exceeds token limit
                    max_token_limit = finbert_esg.config.max_position_embeddings
                    tokens = tokenizer_esg.encode(translated_summary, max_length=max_token_limit-2, truncation=True)

                    # Perform FinBERT-ESG classification on the translated summary
                    esg_results = nlp_esg([tokenizer_esg.decode(tokens)])

                    # Extract ESG label and score
                    esg_label = esg_results[0].get('label', 'Not ESG Related')  # Replace 'None' with 'Not ESG Related'
                    esg_score = esg_results[0].get('score', 0.0)

                    # Skip if the article is "Not ESG Related"
                    if esg_label == "Not ESG Related":
                        continue

                    # Update the existing ESG9 field in the MongoDB document
                    collection.update_one(
                        {"_id": _id},
                        {"$set": {"ESG9": {"Label": esg_label, "Score": esg_score}}}
                    )

                    classify_ESG9_logger.info(f"FinBERT-ESG9 classification completed for document {_id}. Label: {esg_label}, Score: {esg_score}")

                    esg_labels_added += 1

                # Break the loop if all documents have been processed
                break

            except pymongo.errors.CursorNotFound:
                classify_ESG9_logger.error("Cursor lost. Restarting from last processed document ID.")
                continue  # This continues the while loop, recreating the cursor

        print(f"ESG9 Classification complete. {esg_labels_added} labels added to the collection.")
        classify_ESG9_logger.info(f'=== Script execution END (ESG9 Classification) at: {datetime.now()} with {esg_labels_added} labels added to the collection ===')

    except Exception as e:
        classify_ESG9_logger.error(f"Error during ESG9 classification: {str(e)}")

    return esg_labels_added

def classify_FLS(skip_existing=False):
    classify_FLS_logger.info(f'=== Script execution START (FLS Classification) at: {datetime.now()} ===')

    last_processed_id = None  # Keep track of the last processed document ID
    fls_labels_added = 0  # Initialize count

    try:
        # Load FinBERT-FLS model and tokenizer
        finbert_fls = BertForSequenceClassification.from_pretrained('yiyanghkust/finbert-fls', num_labels=3)
        tokenizer_fls = BertTokenizer.from_pretrained('yiyanghkust/finbert-fls')
        nlp_fls = pipeline("text-classification", model=finbert_fls, tokenizer=tokenizer_fls)

        # Connect to MongoDB
        collection = connect_to_mongo_atlas()
        total_documents = collection.count_documents({})  # Use count_documents method on the collection

        while True:
            try:
                # If the cursor was lost, start from the next document
                if last_processed_id:
                    cursor = collection.find({"_id": {"$gt": last_processed_id}})
                else:
                    cursor = collection.find()

                for document in tqdm(cursor, desc="Processing Articles", total=total_documents):
                    _id = document["_id"]
                    last_processed_id = _id  # Update the last processed document ID

                    # Skip if skip_existing is True and FLS label already exists
                    if skip_existing and 'FLS' in document:
                        continue

                    translated_summary = document.get("Translated Summary", "")

                    # Check if summary exceeds token limit
                    max_token_limit = finbert_fls.config.max_position_embeddings
                    tokens = tokenizer_fls.encode(translated_summary, max_length=max_token_limit-2, truncation=True)

                    # Perform FinBERT-FLS classification on the translated summary
                    fls_results = nlp_fls([tokenizer_fls.decode(tokens)])

                    # Extract FinBERT-FLS label and score
                    fls_label = fls_results[0].get('label', 'Not FLS Related')
                    fls_score = fls_results[0].get('score', 0.0)

                    # Update the existing FLS field in the MongoDB document
                    collection.update_one(
                        {"_id": _id},
                        {"$set": {"FLS": {"Label": fls_label, "Score": fls_score}}}
                    )

                    classify_FLS_logger.info(f"FinBERT-FLS classification completed for document {_id}. Label: {fls_label}, Score: {fls_score}")

                    fls_labels_added += 1

                # Break the loop if all documents have been processed
                break

            except pymongo.errors.CursorNotFound:
                classify_FLS_logger.error("Cursor lost. Restarting from last processed document ID.")
                continue  # This continues the while loop, recreating the cursor

        print(f"FinBERT-FLS Classification complete. {fls_labels_added} labels added to the collection.")
        classify_FLS_logger.info(f'=== Script execution END (FLS Classification) at: {datetime.now()} with {fls_labels_added} labels added to the collection ===')

    except Exception as e:
        classify_FLS_logger.error(f"Error during FinBERT-FLS classification: {str(e)}")

    return fls_labels_added


def classify_NER():
    classify_NER_logger.info(f'=== Script execution START (NER Classification) at: {datetime.now()} ===')

    try:
        # Load Flair NER model
        tagger = SequenceTagger.load("flair/ner-english-ontonotes-large")

        # Connect to MongoDB
        collection = connect_to_mongo_atlas()
        cursor = collection.find()

        ner_entities_added = 0  # Initialize count
        documents_updated = 0

        global_entities = set()  # Initialize global set of entities

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
            entities = [(entity.tag, entity.text) for entity in sentence.get_spans('ner')]

            # Filter entities to include only ORG and GPE
            filtered_entities = [(entity_tag, entity_text) for entity_tag, entity_text in entities if entity_tag in ["ORG", "GPE"]]

            # Convert list of tuples to a set to remove duplicates
            unique_entities = set(filtered_entities)

            # Check if there are no ORG or GPE entities
            if not unique_entities:
                # Update MongoDB document with "None detected"
                collection.update_one(
                    {"_id": _id},
                    {"$set": {"Entities": "None detected"}}
                )
                classify_NER_logger.info(f"No ORG or GPE entities detected for document {_id}. Updated with 'None detected'.")
            else:
                # Convert the set back to a list
                entities_to_add = [entity_text for _, entity_text in unique_entities]

                # Update the MongoDB document with unique detected entities
                collection.update_one(
                    {"_id": _id},
                    {"$set": {"Entities": entities_to_add}}
                )

                classify_NER_logger.info(f"NER classification completed for document {_id}. Unique entities added: {entities_to_add}")

                ner_entities_added += len(filtered_entities)
                # Increment the documents updated counter
                documents_updated += 1


        print(f"NER Classification complete.{documents_updated} documents updated in the collection. {ner_entities_added} entities added to the collection.")
        classify_NER_logger.info(f'=== Script execution END (NER Classification) at: {datetime.now()} with {documents_updated} documents updated in the collection and a total of {ner_entities_added} entities added to the collection ===')

    except Exception as e:
        classify_NER_logger.error(f"Error during NER classification: {str(e)}")

    return ner_entities_added
