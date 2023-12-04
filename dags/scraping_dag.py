from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime

start_date = datetime(2023, 10, 15, 21, 40, 0)  # Year, Month, Day, Hour, Minute, Second

# Other default arguments for your DAG
default_args = {
    'owner': 'Sparda',
    'start_date': start_date,  # Set the exact start date here
    'retries': 1,
}

dag = DAG(
    'OLD_SCRAPING_DAG',
    default_args=default_args,
    schedule_interval="@daily",  # Set this to None to disable automatic scheduling
    catchup=False,
)

def run_scraping_script():
    import subprocess
    language = "FR"  # Set the language to French
    insert_method = "auto"  # Set the insertion method to auto
    # Execute your script with the provided arguments
    script_location = '/src/main.py'
    command = ['python', script_location, '--scrap', language, insert_method]
    subprocess.run(command, check=True)

scraping_task = PythonOperator(
    task_id='NSCRAPING_TASK',
    python_callable=run_scraping_script,
    dag=dag,
)
