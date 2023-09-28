# Business Intelligence and Deep Learning Project

## Project Overview
This project merges Business Intelligence (BI) and Deep Learning to scrap and classify news data into "Fake" and "Real" categories. The project is divided into phases for efficient development and execution.


# Progress Checklist:

### I) Setting up the Environment
- Docker: Containerization of the project (Done) ✔
- GitHub: Version control for collaborative development (Done) ✔
- MongoDB: Data storage and management (Done) ✔

### II) Scraping Script
#### Data Scraping Optimization
- Error logging (Done) ✔
- Custom headers (In Progress) 🔧
- User-agent spoofing (In Progress) 🔧
- Request throttling (In Progress) 🔧
- Tor proxy integration (In Progress) 🔧

#### Data Storage and Management in MongoDB
- Data Insertion (Done) ✔
- Duplicate Checking (Done) ✔
- Data Query (Done) ✔
- Data Purging (Done) ✔

### III) Data Classification (Fake/Real)
- Data Preprocessing (To Do) ✘
- Model Development (To Do) ✘
- Model Evaluation (To Do) ✘
- Integration (To Do) ✘

### IV) Data Visualization with Django
- Django Web Application (To Do) ✘
- User-friendly Dashboards (To Do) ✘
- User Authentication (To Do) ✘
- Data Access Control (To Do) ✘
- Deployment (To Do) ✘

# Script Usage:
To manage data in MongoDB using the provided script, you can use the following command-line arguments:

- `--scrap`: Use this argument to initiate data scraping. Specify the desired language for scraping by providing one of the supported language codes (e.g., "EN" for English, "FR" for French, "ES" for Spanish). For example:
  `python script.py --scrap EN`
- `--query`: Use this argument to query the MongoDB collection and retrieve stored data. Execute it as follows:
  `python script.py --query`
- `--purge`: Clear (purge) the MongoDB collection and remove all data by using this argument:
  `python script.py --purge`


