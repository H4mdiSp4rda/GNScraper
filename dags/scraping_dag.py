from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime

start_date = datetime(2023, 10, 15, 21, 40, 0)  # Year, Month, Day, Hour, Minute, Second

# Other default arguments for your DAG
default_args = {
    'owner': 'Sp4rda',
    'start_date': start_date,  # Set the exact start date here
    'retries': 1,
}

dag = DAG(
    'news_scraping_dag',
    default_args=default_args,
    schedule_interval=None,  # Set this to None to disable automatic scheduling
    catchup=False,
)

def run_scraping_script(language, insert_method):
    import subprocess

    # Execute your script with the provided arguments
    script_location = '/gns_code/scrap.py'
    command = ['python', script_location, '--scrap', language, insert_method]
    subprocess.run(command, check=True)

scraping_task = PythonOperator(
    task_id='scrape_news',
    python_callable=run_scraping_script,
    op_args=['auto'],  # Define your arguments here
    dag=dag,
)
