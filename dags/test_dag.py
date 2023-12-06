from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator

default_args = {
    'owner': 'bi_student',
    'depends_on_past': False,
    'start_date': datetime(2023, 4, 12),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'hello_world_dag',
    default_args=default_args,
    description='A simple DAG to print Hello World',
    schedule_interval=timedelta(days=1),  # Change as per your requirements
)

# Task 1
def print_hello():
    print("Hello")

task_hello = PythonOperator(
    task_id='print_hello',
    python_callable=print_hello,
    dag=dag,
)

# Task 2
def print_world():
    print("World")

task_world = PythonOperator(
    task_id='print_world',
    python_callable=print_world,
    dag=dag,
)

# Define the task dependencies
task_hello >> task_world
