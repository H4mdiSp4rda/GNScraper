from gevent import monkey
monkey.patch_all(thread=False, select=False)

import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

def setup_logging(log_name, base_log_file_name):
    # Get or create a logger
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)

    # Create a log formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Generate log file name with current date
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_file_name = f"{base_log_file_name}-{current_date}.log"
    log_file_path = f"./logs/GNS_logs/{log_file_name}"

    # Set up a timed rotating file handler
    file_handler = TimedRotatingFileHandler(log_file_path, when='midnight', interval=1, backupCount=5)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)

    return logger
