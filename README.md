# Business Intelligence and Deep Learning Project

## Project Overview
This project merges Business Intelligence (BI) and Deep Learning to scrap and classify news data into "Fake" and "Real" categories. The project is divided into phases for efficient development and execution.


# Progress Checklist:

### I) Setting up the Environment
- Docker: Containerization of the project (Done) ✔
- GitHub: Version control for collaborative development (Done) ✔
- MongoDB: Data storage and management (Done) ✔

### II) Scraping Script
#### Data Scraping
- Error logging (Work in progress) 🔨
- Custom headers (Done) ✔
- User-agent spoofing (Done) ✔
- Request throttling (Done) ✔
- Tor proxy integration (Abandoned due to client request) ✘
- Multi-threading (Work in progress) 🔨
- Automation with Airflow (Work in progress) 🔨

#### Data Storage and Management in MongoDB
- Data Insertion (Done) ✔
- Duplicate Checking (Done) ✔
- Data Query (Done) ✔
- Data Purging (Done) ✔

### III) Data Classification (Fake/Real)
- Model Development (Done) ✔
- Model Evaluation (Done) ✔
- Integration (Done) ✔

### IV) Data Visualization with Django
- Django Web Application (To Do) ✘
- User-friendly Dashboards (To Do) ✘
- User Authentication (To Do) ✘
- Data Access Control (To Do) ✘
- Deployment (To Do) ✘

# Script Usage:
To manage data in MongoDB using the provided script, you can use the following command-line arguments:

- `--scrap`: Use this argument to initiate data scraping. Specify the desired language for scraping by providing one of the supported language codes (e.g., "EN" for English, "FR" for French, "ES" for Spanish). You must also specify the insertion method as "auto" or "manual" to decide whether to store the scraped data in the database automatically or prompt for confirmation. Example usage:
  `python script.py --scrap EN auto`
- `--query`: Use this argument to query the MongoDB collection and retrieve stored data.
- `--purge`: Clear (purge) the MongoDB collection and remove all data by using this argument.
- `--classify`: Classify the news articles in MongoDB and add a label (Real news/Fake news) to each one.


