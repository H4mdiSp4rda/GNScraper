from gevent import monkey
monkey.patch_all(thread=False, select=False)

import logging
from logging.handlers import RotatingFileHandler


def setup_logging(log_name, log_file_path):
    # Get or create a logger
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)

    # Create a log formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Set up a rotating file handler
    file_handler = RotatingFileHandler(log_file_path, maxBytes=10 * 1024 * 1024, backupCount=5)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)

    return logger
