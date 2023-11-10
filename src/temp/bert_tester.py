from gevent import monkey
monkey.patch_all(thread=False, select=False)


import numpy as np
import pandas as pd
from transformers import AutoModel, BertTokenizerFast
import torch
import torch.nn as nn
from sklearn.metrics import classification_report
from pymongo import MongoClient


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


def test_unseen_data(texts):
    MAX_LENGTH = 15
    tokens_unseen = tokenizer.batch_encode_plus(
        texts,
        max_length=MAX_LENGTH,
        pad_to_max_length=True,
        truncation=True
    )

    unseen_seq = torch.tensor(tokens_unseen['input_ids'])
    unseen_mask = torch.tensor(tokens_unseen['attention_mask'])

    with torch.no_grad():
        preds = model(unseen_seq, unseen_mask)
        preds = preds.detach().cpu().numpy()

    predictions = np.argmax(preds, axis=1)
    return predictions


unseen_news_text = [
    "Donald Trump Sends Out Embarrassing New Year’s Eve Message; This is Disturbing",  # Fake
    "WATCH: George W. Bush Calls Out Trump For Supporting White Supremacy",  # Fake
    "U.S. lawmakers question businessman at 2016 Trump Tower meeting: sources",  # True
    "Trump administration issues new rules on U.S. visa waivers",  # True
    "Scientists Discover New Species of Rare Bird in Amazon Rainforest",  # True
    "Aliens Spotted Over New York City Skyline, Experts Weigh In",  # Fake
    "World Health Organization Declares Global Pandemic",  # True
    "Local Bakery Wins National Pie-Making Contest",  # True
    "Elvis Presley Spotted at Local Diner: Is The King Alive?",  # Fake
    "Stock Market Hits All-Time High Amid Economic Recovery",  # True
]

predictions = test_unseen_data(unseen_news_text)
print(predictions)
