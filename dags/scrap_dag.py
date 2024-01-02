from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash_operator import BashOperator

# DAG configuration
default_args = {
    'owner': 'sparda',
    'depends_on_past': False,
    'start_date': datetime(2023, 12, 31),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG('NEWS_SCRAPING_DAG',
          default_args=default_args,
          description='Scraps news data with a daily interval',
          schedule_interval=timedelta(days=1))

# Define the task
scrape_task = BashOperator(
    task_id='scrape_news',
    bash_command='python /gns_code/src/main.py --scrap FR auto',
    dag=dag)

scrape_task
