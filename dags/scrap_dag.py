from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash_operator import BashOperator

# DAG configuration
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 12, 31),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG('scrape_news_dag',
          default_args=default_args,
          description='A simple DAG to scrape news data',
          schedule_interval=timedelta(days=1))

# Define the task
scrape_task = BashOperator(
    task_id='scrape_news',
    bash_command='docker exec 24d0956eb1d4853d64691beceb0bd948f1f7ca2622040b60aa11f3d5f430b5c8 python /gns_code/src/scrap.py --scrap FR auto',
    dag=dag)

scrape_task
