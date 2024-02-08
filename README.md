# Business Intelligence and Deep Learning Project

## Project Overview
This project merges BI and Deep Learning to extract insights from financial news articles. The project is divided into phases for efficient development and execution.


# Progress Checklist:

### I) Setting up the Environment
- Docker: Containerization of the project (Done) ✔
- GitHub: Version control for collaborative development (Done) ✔
- MongoDB: Data storage and management (Done) ✔

### II) Scraping Script
#### Data Scraping
- Error logging (Done) ✔
- Custom headers (Done) ✔
- User-agent spoofing (Done) ✔
- Request throttling (Done) ✔
- Tor proxy integration (Abandoned due to client request) ✘
- Asynchronous Scraping (Done) ✔
- Automation with Airflow (Done) ✔

#### Data Storage and Management in MongoDB
- Data Insertion (Done) ✔
- Duplicate Checking (Done) ✔
- Data Query (Done) ✔
- Data Purging (Done) ✔
- Data Back-up Automation (Work in progress) 🔨

### III) Data Classification (Fake/Real)
- Data Preprocessing (Done) ✔
- Model Development (Done) ✔
- Model Fine-Tuning (Done) ✔
- Model Evaluation (Done) ✔
- Integration (Done) ✔

### IV) Opportunity & Threats Analysis
- Sentiment Analysis (Done) ✔
- ESG Analysis (Done) ✔
- Forward Looking Statements Analysis (Done) ✔
- Named Entity Recognition (Done) ✔
- FinGPT Integration (To Do) ✘

### V) Data Visualization with Django
- Django Web Application (Work in progress) 🔨
- User-friendly Dashboards (Work in progress) 🔨
- Data Access Control (To Do) ✘
- Deployment (To Do) ✘

# Script Usage:
To manage data in MongoDB using the provided script, you can use the following command-line arguments:

- `--scrap`: Use this argument to initiate data scraping. Specify the desired language for scraping by providing one of the supported language codes (e.g., "EN" for English, "FR" for French, "ES" for Spanish). You must also specify the insertion method as "auto" or "manual" to decide whether to store the scraped data in the database automatically or prompt for confirmation. <br> 
Example usage:
  `python main.py --scrap EN auto`
- `--query`: Use this argument to query the MongoDB collection and retrieve stored data.
- `--purge`: Clear (purge) the MongoDB collection and remove all data by using this argument.
- `--classify`: Classify the news articles in MongoDB. Use the following sub args (R/F, SA, ESG, ESG9, FLS, NER). Add the sub-argument "skip" if you wish to skip already classified documents. <br>
Example usage:
  `python main.py --classify ESG skip`