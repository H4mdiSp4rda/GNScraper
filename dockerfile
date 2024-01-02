# Use an official Python runtime as a parent image
#FROM python:3.10.13-slim
FROM apache/airflow:2.8.0-python3.10


# Set environment variables 
#ENV APP_HOME /app
#ENV PYTHONUNBUFFERED 1

# Create the application directory
#RUN mkdir $APP_HOME
WORKDIR /gns_code

# Install system dependencies 
RUN pip install setuptools==58



# Install project dependencies
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --upgrade feedparser
RUN pip install --upgrade requests
RUN pip install --upgrade translators
COPY ./utils/setup_nltk.py ./
RUN ./utils/setup_nltk.py


# Copy your scraping script and other project files into the container
#COPY . ./

# Expose any necessary ports
# EXPOSE <port>

# Define the command to run when the container starts
#CMD ["python", "./src/scrap.py"]
