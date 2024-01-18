gsutil cp huggingface_dag.py gs://us-east1-production-cc2-202-b42a7a54-bucket/dags/
gsutil cp sequences/* gs://us-east1-production-cc2-202-b42a7a54-bucket/dags/sequences/huggingface/
gsutil rm gs://us-east1-production-cc2-202-b42a7a54-bucket/dags/sql/huggingface/*
gsutil cp sql/* gs://us-east1-production-cc2-202-b42a7a54-bucket/dags/sql/huggingface/
gsutil cp schemas/* gs://us-east1-production-cc2-202-b42a7a54-bucket/dags/schemas/huggingface/
gsutil rm -r gs://airflow-data-exchange/huggingface/schemas/*
gsutil cp schemas/* gs://airflow-data-exchange/huggingface/schemas/
gsutil -m cp -r huggingface_scripts/* gs://us-east1-production-cc2-202-b42a7a54-bucket/dags/huggingface_scripts/