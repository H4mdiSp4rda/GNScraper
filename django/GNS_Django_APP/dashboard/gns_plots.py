import pandas as pd
import plotly.express as px
from plotly.offline import plot
import pymongo


# Should be replaced with env variables
# MongoDB Atlas Configuration
MONGODB_ATLAS_USERNAME = "Sp4rda"
MONGODB_ATLAS_PASSWORD = "CuIHqKlU8dFzZ4zt"
MONGODB_ATLAS_CLUSTER = "gns-db"
MONGODB_ATLAS_DB_NAME = "gns_mongodb"
MONGODB_ATLAS_URI = f"mongodb+srv://{MONGODB_ATLAS_USERNAME}:{MONGODB_ATLAS_PASSWORD}@{MONGODB_ATLAS_CLUSTER}.g93kgy3.mongodb.net/{MONGODB_ATLAS_DB_NAME}?retryWrites=true&w=majority"
COLLECTION_NAME = "articles"


def connect_to_mongo_atlas():
    try:
        client = pymongo.MongoClient(MONGODB_ATLAS_URI)
        db = client[MONGODB_ATLAS_DB_NAME]
        collection = db[COLLECTION_NAME]
        return collection
    except Exception as e:
        print(f"An error occurred while connecting to MongoDB Atlas: {e}")
        return None



def visualize_data():
    # Connect to MongoDB and retrieve data
    collection = connect_to_mongo_atlas()
    cursor = collection.find()

    # Create a Pandas DataFrame from MongoDB data
    df = pd.DataFrame(list(cursor))

    # Store HTML components for each visualization
    visualizations = {}

    # Visualize a bar chart of sentiment labels
    sentiment_fig = px.histogram(df, x="Sentiment Label", color="Sentiment Label", title="Distribution of Sentiment Labels")
    visualizations['sentiment_chart'] = plot(sentiment_fig, output_type='div', include_plotlyjs=False)

    # Visualize a pie chart of ESG labels
    esg_labels = df['ESG']  # ESG contains simple strings
    esg_value_counts = esg_labels.value_counts()

    if not esg_value_counts.empty:
        esg_fig = px.pie(values=esg_value_counts, names=esg_value_counts.index, title="Distribution of ESG Labels")
        visualizations['esg_chart'] = plot(esg_fig, output_type='div', include_plotlyjs=False)

    # Visualize a pie chart of ESG9 labels
    esg9_labels = df['ESG9'].apply(lambda x: x['Label'] if isinstance(x, dict) and 'Label' in x else None)
    esg9_value_counts = esg9_labels.value_counts()

    if not esg9_value_counts.empty:
        esg9_fig = px.pie(values=esg9_value_counts, names=esg9_value_counts.index, title="Distribution of ESG9 Labels")
        visualizations['esg9_chart'] = plot(esg9_fig, output_type='div', include_plotlyjs=False)

    # Visualize a pie chart of FLS labels
    fls_labels = df['FLS'].apply(lambda x: x['Label'] if isinstance(x, dict) and 'Label' in x else None)
    fls_value_counts = fls_labels.value_counts()

    if not fls_value_counts.empty:
        fls_fig = px.pie(values=fls_value_counts, names=fls_value_counts.index, title="Distribution of FLS Labels")
        visualizations['fls_chart'] = plot(fls_fig, output_type='div', include_plotlyjs=False)

    return visualizations


def aggregate_sentiment_by_entity():
    collection = connect_to_mongo_atlas()

    # MongoDB aggregation pipeline
    pipeline = [
        {
            '$unwind': '$Entities'
        },
        {
            '$match': {
                'Sentiment Label': {'$in': ['Positive', 'Negative']}  # Filtering out neutral sentiments
            }
        },
        {
            '$group': {
                '_id': {
                    'Entity': '$Entities',
                    'Sentiment': '$Sentiment Label'
                },
                'Count': {'$sum': 1}
            }
        },
        {
            '$sort': {'_id.Entity': 1, '_id.Sentiment': 1}
        }
    ]

    try:
        results = list(collection.aggregate(pipeline))
        return results
    except Exception as e:
        print(f"An error occurred during aggregation: {e}")
        return []

def prepare_sentiment_data_for_visualization(aggregated_data):
    # Transform the aggregated data into a format suitable for visualization
    data = {
        'Entity': [],
        'Sentiment': [],
        'Count': []
    }

    for item in aggregated_data:
        data['Entity'].append(item['_id']['Entity'])
        data['Sentiment'].append(item['_id']['Sentiment'])
        data['Count'].append(item['Count'])

    df = pd.DataFrame(data)
    return df


def visualize_sentiment_distribution(df):
    fig = px.bar(df, x='Entity', y='Count', color='Sentiment', title='Sentiment Distribution Across Entities', barmode='group')
    fig.show()


def get_top_positive_entities():
    collection = connect_to_mongo_atlas()

    # MongoDB aggregation pipeline
    pipeline = [
        {
            '$unwind': '$Entities'
        },
        {
            '$match': {
                'Sentiment Label': 'Positive',  # Filter for positive sentiments
                'Entities': {'$ne': "None detected"}  # Exclude documents where Entities is "None detected"
            }
        },
        {
            '$group': {
                '_id': '$Entities',
                'Count': {'$sum': 1}
            }
        },
        {
            '$sort': {'Count': -1}  # Sort by count in descending order
        },
        {
            '$limit': 10  # Limit to top 10
        }
    ]

    try:
        results = list(collection.aggregate(pipeline))
        return results
    except Exception as e:
        print(f"An error occurred during aggregation: {e}")
        return []

def prepare_positive_entities_data_for_visualization(aggregated_data):
    entities = [item['_id'] for item in aggregated_data]
    counts = [item['Count'] for item in aggregated_data]

    return entities, counts

def visualize_top_positive_entities(entities, counts):
    fig = px.bar(x=entities, y=counts, labels={'x': 'Entity', 'y': 'Count'}, title='Top 10 Entities with Positive Sentiment')
    fig.update_layout(xaxis_title='Entity', yaxis_title='Positive Sentiment Count')
    fig.show()


def get_top_negative_entities():
    collection = connect_to_mongo_atlas()

    # MongoDB aggregation pipeline
    pipeline = [
        {
            '$unwind': '$Entities'
        },
        {
            '$match': {
                'Sentiment Label': 'Negative',  # Filter for negative sentiments
                'Entities': {'$nin': ["House", "Congress", "None detected", "the European Union", "GOP", "AFP", "Reuters", "State", "the Public Prosecution", "National Bank", "Parliament", 'Liberation', "the Board of Directors"]}  # Exclude "House" and "Congress" from entities
            }
        },
        {
            '$group': {
                '_id': '$Entities',
                'Count': {'$sum': 1}
            }
        },
        {
            '$sort': {'Count': -1}  # Sort by count in descending order
        },
        {
            '$limit': 10  # Limit to top 10
        }
    ]

    try:
        results = list(collection.aggregate(pipeline))
        return results
    except Exception as e:
        print(f"An error occurred during aggregation: {e}")
        return []
def prepare_negative_entities_data_for_visualization(aggregated_data):
    entities = [item['_id'] for item in aggregated_data]
    counts = [item['Count'] for item in aggregated_data]

    return entities, counts

def visualize_top_negative_entities(entities, counts):
    fig = px.bar(x=entities, y=counts, labels={'x': 'Entity', 'y': 'Count'}, title='Top 10 Entities with Negative Sentiment')
    fig.update_layout(xaxis_title='Entity', yaxis_title='Negative Sentiment Count', color_continuous_scale=px.colors.sequential.Viridis)
    fig.show()
