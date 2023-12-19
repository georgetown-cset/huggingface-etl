FROM ubuntu:latest

# Set up system dependencies
RUN apt -y update
RUN apt-get -y update
RUN apt-get install -y build-essential libssl-dev libffi-dev python3-dev python3-pip curl

# Grab files we need to run
ADD requirements.txt /huggingface/requirements.txt
ADD huggingface_scripts/* /huggingface/

# install gsutil and put it on the path for airflow to use
ENV CLOUDSDK_INSTALL_DIR /usr/local/gcloud/
RUN curl -sSL https://sdk.cloud.google.com | bash
ENV PATH $PATH:/usr/local/gcloud/google-cloud-sdk/bin

# Install python dependencies
WORKDIR /huggingface
ENV AIRFLOW_GPL_UNIDECODE=yes
RUN pip3 install -r requirements.txt
# Make sure the above config succeeded
RUN python3 -m pytest test_clean_data.py -k test_fix_model_index