from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash_operator import BashOperator

default_args = {
    'owner': 'Sparda',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'NEWS_SCRAPING',
    default_args=default_args,
    description='DAG to run the scraping functionality',
    schedule_interval=timedelta(days=1),  # Change as per your requirements
)

# def run_scraping():
#     try:
#         # Replace this with the actual path to your main.py script
#         script_path = "/gns_code/src/main.py"
#         command = f"/src/main.py --scrap FR auto"
        
#         # Execute the scraping command
#         import subprocess
#         result = subprocess.run("python ./src/main.py --scrap FR auto", shell=True, check=True, capture_output=True)
#         # Log the script output
#         print(result.stdout.decode())
#         print(result.stderr.decode())
#     except Exception as e:
#         print(f"Error during scraping: {str(e)}")
#         raise

# scraping_task = PythonOperator(
#     task_id='NEWS_SCRAPING_TASK',
#     python_callable=run_scraping,
#     dag=dag,
# )


t1 = BashOperator(
    task_id='run_python_script',
    bash_command='python /gns_code/src/main.py --scrap EN auto',
    dag=dag)

# Set task dependencies if needed
# For example, if you have other tasks to run before scraping, uncomment and modify the following line:
# scraping_task.set_upstream(other_task)

# It's good practice to explicitly set the task dependencies using set_downstream
# This helps in DAG visualization and ensures a clear execution order
# other_task.set_downstream(scraping_task)
