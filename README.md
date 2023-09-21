# Business Intelligence and Deep Learning Project

## Project Overview
This project aims to leverage Business Intelligence (BI) techniques and Deep Learning algorithms to scrap, analyze and classify news data into two categories: Fake and Real. The project is divided into several main parts for efficient development and execution.

### I) Setting up the Environment
The initial phase of the project involves setting up the development environment. This phase includes the following subtasks, which have already been completed:
- Docker: Containerization of the project
- GitHub: Version control for collaborative development
- MongoDB: Data storage and management

### II) Scraping Script
In this phase, we will focus on developing a robust web scraping script to gather data for analysis. This phase includes the following tasks:

1. **Data Scraping Optimization**:
   - Implementation of various optimizations such as custom headers, user-agent spoofing, driver-agent, request throttling, and Tor proxy integration to avoid IP blocking and improve scraping efficiency.

2. **Data Storage and Management in MongoDB**:
   - **Data Insertion**: Already completed.
   - **Data Update**: Already completed.
   - **Duplicate Checking**: Already completed. Implement logic to identify and eliminate duplicate data entries.
   - **Data Query**: Already completed. Create queries to retrieve relevant data from the MongoDB database.
   - **Data Purging**: Already completed. Develop a mechanism to remove outdated or irrelevant data from the database.

### III) Data Classification
This phase focuses on using Deep Learning techniques to classify the scraped data into two categories: Fake and Real. This classification will help in identifying potentially misleading or inaccurate information. The specific tasks in this phase include:

- Data Preprocessing: Prepare the scraped data for input into deep learning models. This may include text cleaning, feature extraction, and data transformation.
- Model Development: Build and train deep learning models for the classification task. Experiment with various architectures, such as convolutional neural networks (CNNs) or recurrent neural networks (RNNs), and select the best-performing model.
- Model Evaluation: Assess the performance of the classification models using relevant metrics (e.g., accuracy, precision, recall, F1-score).
- Integration: Integrate the classification model into the project pipeline to automate the categorization of scraped data.

### IV) Data Visualization with Django
The final phase of the project involves creating a web-based data visualization interface using the Django framework. This interface will allow users to interactively explore the analyzed data. The tasks in this phase include:

- Building a Django web application that connects to the MongoDB database.
- Developing user-friendly dashboards and visualizations to present the results of the data classification.
- Implementing features for user authentication and data access control.
- Deploying the Django application to a web server for remote access.

# Progress Checklist:

### I) Setting up the Environment
- Docker: Containerization of the project (Done) ✔
- GitHub: Version control for collaborative development (Done) ✔
- MongoDB: Data storage and management (Done) ✔

### II) Scraping Script
#### Data Scraping Optimization
- Custom headers (Needs Work) ✘
- User-agent spoofing (Needs Work) ✘
- Request throttling (Needs Work) ✘
- Tor proxy integration (Needs Work) ✘

#### Data Storage and Management in MongoDB
- Data Insertion (Done) ✔
- Data Update (Done) ✔
- Duplicate Checking (Done) ✔
- Data Query (Done) ✔
- Data Purging (Done) ✔

### III) Data Classification (Fake/Real)
- Data Preprocessing (Needs Work) ✘
- Model Development (Needs Work) ✘
- Model Evaluation (Needs Work) ✘
- Integration (Needs Work) ✘

### IV) Data Visualization with Django
- Django Web Application (Needs Work) ✘
- User-friendly Dashboards (Needs Work) ✘
- User Authentication (Needs Work) ✘
- Data Access Control (Needs Work) ✘
- Deployment (Needs Work) ✘

# Script Usage:
- How to manage data in MongoDB:
    - `--scrap`: Scrap data
    - `--query`: Query the MongoDB collection
    - `--purge`: Purge (clear) the MongoDB collection


