from gevent import monkey
monkey.patch_all(thread=False, select=False)


import numpy as np
import pandas as pd
from transformers import AutoModel, BertTokenizerFast
import torch
import torch.nn as nn
from sklearn.metrics import classification_report
from mongo_ops import connect_to_mongodb


# Load your BERT model and tokenizer
bert = AutoModel.from_pretrained('bert-base-uncased')
tokenizer = BertTokenizerFast.from_pretrained('bert-base-uncased')

# Define the BERT model architecture
class BERT_Arch(nn.Module):
    def __init__(self, bert):
        super(BERT_Arch, self).__init__()
        self.bert = bert
        self.dropout = nn.Dropout(0.1)
        self.relu = nn.ReLU()
        self.fc1 = nn.Linear(768, 512)
        self.fc2 = nn.Linear(512, 2)
        self.softmax = nn.LogSoftmax(dim=1)

    def forward(self, sent_id, mask):
        cls_hs = self.bert(sent_id, attention_mask=mask)['pooler_output']
        x = self.fc1(cls_hs)
        x = self.relu(x)
        x = self.dropout(x)
        x = self.fc2(x)
        x = self.softmax(x)
        return x

# Load the BERT model and weights
model = BERT_Arch(bert)
model.load_state_dict(torch.load('./data/bert/c2_new_model_weights.pt'))
model.eval()

# Function to classify a list of texts
def classify_texts(texts):
    # Tokenize and encode sequences
    MAX_LENGTH = 15
    tokens = tokenizer.batch_encode_plus(
        texts,
        max_length=MAX_LENGTH,
        pad_to_max_length=True,
        truncation=True
    )

    seq = torch.tensor(tokens['input_ids'])
    mask = torch.tensor(tokens['attention_mask'])

    with torch.no_grad():
        preds = model(seq, mask)
        preds = preds.detach().cpu().numpy()

    labels = np.argmax(preds, axis=1)
    return labels


def classify_and_update_mongodb():
    try:
        # Connect to your MongoDB database
        collection = connect_to_mongodb()

        # Retrieve the articles with translated titles
        articles = collection.find({}, {"_id": 1, "Translated Title": 1})

        for article in articles:
            text = article["Translated Title"]
            labels = classify_texts([text])  # Use your classification function here

            Label = "Fake news" if labels[0] == 1 else "Real news"

            # Update the collection with the label
            collection.update_one({"_id": article["_id"]}, {"$set": {"label": label}})
        
        print("Classification and MongoDB update complete.")

    except Exception as e:
        print(f"An error occurred during classification and update: {e}")
