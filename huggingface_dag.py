import os
from datetime import datetime
import json

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.providers.google.cloud.transfers.bigquery_to_bigquery import BigQueryToBigQueryOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator, BigQueryCheckOperator
from airflow.providers.google.cloud.operators.cloud_sql import (
    CloudSQLImportInstanceOperator,
)
from airflow.providers.google.cloud.operators.kubernetes_engine import GKEStartPodOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.operators.dummy import DummyOperator
from airflow.providers.google.cloud.operators.gcs import GCSDeleteObjectsOperator
from airflow.providers.google.cloud.transfers.bigquery_to_gcs import (
    BigQueryToGCSOperator,
)
from dataloader.airflow_utils.defaults import (
    DATA_BUCKET,
    PROJECT_ID,
    GCP_ZONE,
    get_default_args,
    get_post_success,
)
from dataloader.scripts.populate_documentation import update_table_descriptions

bucket = DATA_BUCKET
production_dataset = "huggingface"
staging_dataset = f"staging_{production_dataset}"
backups_dataset = f"{production_dataset}_backups"
sql_dir = f"sql/{production_dataset}"
schema_dir = f"{production_dataset}/schemas"
tmp_dir = f"{production_dataset}/tmp"

default_args = get_default_args()
date = datetime.now().strftime("%Y%m%d")


# Part 2: Get data from airtable and update databases
dag = DAG(
    "huggingface",
    default_args=default_args,
    description="Hugging Face data scraper and updater",
    schedule_interval=None,
    catchup=False,
    user_defined_macros={
        "staging_dataset": staging_dataset,
        "production_dataset": production_dataset,
        "backups_dataset": backups_dataset
    },
)
with dag:

    clear_tmp_dir = GCSDeleteObjectsOperator(
        task_id="clear_tmp_dir",
        bucket_name=DATA_BUCKET,
        prefix=tmp_dir
    )

    # run the huggingface scraper

    run_extract_data = GKEStartPodOperator(
        task_id="run_extract_data",
        project_id=PROJECT_ID,
        location=GCP_ZONE,
        cluster_name="us-east1-production2023-cc1-01d75926-gke",
        name="run_extract_data",
        cmds=["/bin/bash"],
        arguments=["-c", (f"echo 'extracting hugging face data!' ; rm -r data || true ; "
                          f"mkdir -p data && "
                          f"python3 extract_data.py data && "
                          f"gsutil -m cp -r data/* gs://{DATA_BUCKET}/{tmp_dir}/ ")],
        namespace="default",
        image=f"us.gcr.io/{PROJECT_ID}/huggingface",
        get_logs=True,
        startup_timeout_seconds=300,
        # see also https://cloud.google.com/composer/docs/how-to/using/using-kubernetes-pod-operator#affinity-config
        affinity={
            "nodeAffinity": {
                "requiredDuringSchedulingIgnoredDuringExecution": {
                    "nodeSelectorTerms": [{
                        "matchExpressions": [{
                            "key": "cloud.google.com/gke-nodepool",
                            "operator": "In",
                            "values": [
                                "huggingface-pool",
                            ]
                        }]
                    }]
                }
            }
        }
    )

    # clean the huggingface data

    run_clean_data = GKEStartPodOperator(
        task_id="run_clean_data",
        project_id=PROJECT_ID,
        location=GCP_ZONE,
        cluster_name="us-east1-production2023-cc1-01d75926-gke",
        name="run_extract_data",
        cmds=["/bin/bash"],
        arguments=["-c", (f"echo 'cleaning hugging face data!' ; rm -r data || true ; "
                          f"mkdir -p data && "
                          f"gsutil -m cp gs://{DATA_BUCKET}/{tmp_dir}/models.jsonl data/. && "
                          f"gsutil -m cp gs://{DATA_BUCKET}/{tmp_dir}/tag_types.jsonl data/. && "
                          f"python3 clean_data.py data/models.jsonl data/tag_types.jsonl data && "
                          f"gsutil -m cp data/models_fixed.jsonl gs://{DATA_BUCKET}/{tmp_dir}/ && "
                          f"gsutil -m cp data/usage.jsonl gs://{DATA_BUCKET}/{tmp_dir}/")],
        namespace="default",
        image=f"us.gcr.io/{PROJECT_ID}/huggingface",
        get_logs=True,
        startup_timeout_seconds=300,
        # see also https://cloud.google.com/composer/docs/how-to/using/using-kubernetes-pod-operator#affinity-config
        affinity={
            "nodeAffinity": {
                "requiredDuringSchedulingIgnoredDuringExecution": {
                    "nodeSelectorTerms": [{
                        "matchExpressions": [{
                            "key": "cloud.google.com/gke-nodepool",
                            "operator": "In",
                            "values": [
                                "default-pool",
                            ]
                        }]
                    }]
                }
            }
        }
    )

    # load the cleaned data into one big table

    load_huggingface_data = GCSToBigQueryOperator(
        task_id=f"load_raw_model",
        bucket=DATA_BUCKET,
        source_objects=[f"{tmp_dir}/models_fixed.jsonl"],
        schema_object=f"{schema_dir}/raw_model.json",
        destination_project_dataset_table=f"{staging_dataset}.raw_model",
        source_format="NEWLINE_DELIMITED_JSON",
        create_disposition="CREATE_IF_NEEDED",
        write_disposition="WRITE_TRUNCATE"
    )

    # load the download and likes counts
    # note: in this table, we write_append instead of write_truncating because we want both the old
    # and the updated counts available because they seem to be monthly counts rather than cumulative

    load_update_counts = GCSToBigQueryOperator(
        task_id=f"load_update_counts",
        bucket=DATA_BUCKET,
        source_objects=[f"{tmp_dir}/usage.jsonl"],
        schema_object=f"{schema_dir}/usage.json",
        destination_project_dataset_table=f"{staging_dataset}.usage",
        source_format="NEWLINE_DELIMITED_JSON",
        create_disposition="CREATE_IF_NEEDED",
        write_disposition="WRITE_APPEND"
    )

    # Run the leaderboard scraper

    run_scrape_leaderboard = GKEStartPodOperator(
        task_id="run_scrape_leaderboard",
        project_id=PROJECT_ID,
        location=GCP_ZONE,
        cluster_name="us-east1-production2023-cc1-01d75926-gke",
        name="run_extract_data",
        cmds=["/bin/bash"],
        arguments=["-c", (f"echo 'scraping hugging face leaderboard!' ; rm -r data || true ; "
                          f"mkdir -p data && "
                          f"python3 scrape_leaderboard.py data && "
                          f"gsutil -m cp data/leaderboard.jsonl gs://{DATA_BUCKET}/{tmp_dir}/")],
        namespace="default",
        image=f"us.gcr.io/{PROJECT_ID}/huggingface",
        get_logs=True,
        startup_timeout_seconds=300,
        # see also https://cloud.google.com/composer/docs/how-to/using/using-kubernetes-pod-operator#affinity-config
        affinity={
            "nodeAffinity": {
                "requiredDuringSchedulingIgnoredDuringExecution": {
                    "nodeSelectorTerms": [{
                        "matchExpressions": [{
                            "key": "cloud.google.com/gke-nodepool",
                            "operator": "In",
                            "values": [
                                "default-pool",
                            ]
                        }]
                    }]
                }
            }
        }
    )

    # load the leaderboard data

    load_leaderboard = GCSToBigQueryOperator(
        task_id=f"load_leaderboard",
        bucket=DATA_BUCKET,
        source_objects=[f"{tmp_dir}/leaderboard.jsonl"],
        schema_object=f"{schema_dir}/leaderboard.json",
        destination_project_dataset_table=f"{staging_dataset}.leaderboard",
        source_format="NEWLINE_DELIMITED_JSON",
        create_disposition="CREATE_IF_NEEDED",
        write_disposition="WRITE_TRUNCATE"
    )

    wait_for_tables = DummyOperator(task_id="wait_for_tables")

    seq_path_prefix = f"{os.environ.get('DAGS_FOLDER')}/sequences/huggingface/"
    query_sequence = "query_sequences.csv"

    curr = load_leaderboard
    production_tables = []
    for line in open(seq_path_prefix + query_sequence).readlines():
        table = line.strip()
        production_tables.append(table)
        table_name = f"{staging_dataset}.{table}"
        next_tab = BigQueryInsertJobOperator(
            task_id=f"create_{table_name}",
            configuration={
                "query": {
                    "query": "{% include '" + f"{sql_dir}/{table}.sql" + "' %}",
                    "useLegacySql": False,
                    "destinationTable": {
                        "projectId": PROJECT_ID,
                        "datasetId": staging_dataset,
                        "tableId": table
                    },
                    "allowLargeResults": True,
                    "createDisposition": "CREATE_IF_NEEDED",
                    "writeDisposition": "WRITE_TRUNCATE"
                }
            },
        )
        curr >> next_tab
        curr = next_tab
    curr >> wait_for_tables

    checks = []
    for query in os.listdir(f"{os.environ.get('DAGS_FOLDER')}/{sql_dir}"):
        if not query.startswith("check_"):
            continue
        checks.append(BigQueryCheckOperator(
            task_id=query.replace(".sql", ""),
            sql=f"{sql_dir}/{query}",
            use_legacy_sql=False
        ))

    production_tables.extend(["usage", "leaderboard"])

    wait_for_checks = DummyOperator(task_id="wait_for_checks")

    success_alert = get_post_success("Hugging Face data update succeeded!", dag)

    wait_for_production_backups = DummyOperator(task_id="wait_for_production_backups")

    with open(f"{os.environ.get('DAGS_FOLDER')}/schemas/{production_dataset}/table_descriptions.json") as f:
        table_desc = json.loads(f.read())
    for table in production_tables:
        prod_table_name = f"{production_dataset}.{table}"
        table_copy = BigQueryToBigQueryOperator(
            task_id=f"copy_{table}_to_production",
            source_project_dataset_tables=[f"{staging_dataset}.{table}"],
            destination_project_dataset_table=prod_table_name,
            create_disposition="CREATE_IF_NEEDED",
            write_disposition="WRITE_TRUNCATE"
        )
        pop_descriptions = PythonOperator(
            task_id="populate_column_documentation_for_" + table,
            op_kwargs={
                "input_schema": f"{os.environ.get('DAGS_FOLDER')}/schemas/{production_dataset}/{table}.json",
                "table_name": prod_table_name,
                "table_description": table_desc[table]
            },
            python_callable=update_table_descriptions
        )
        table_backup = BigQueryToBigQueryOperator(
            task_id=f"back_up_{table}",
            source_project_dataset_tables=[f"{staging_dataset}.{table}"],
            destination_project_dataset_table=f"{backups_dataset}.{table}_{date}",
            create_disposition="CREATE_IF_NEEDED",
            write_disposition="WRITE_TRUNCATE"
        )
        (
            wait_for_tables
            >> checks
            >> wait_for_checks
            >> table_copy
            >> pop_descriptions
            >> table_backup
            >> wait_for_production_backups
        )

    (
        clear_tmp_dir
        >> run_extract_data
        >> run_clean_data
        >> load_huggingface_data
        >> load_update_counts
        >> run_scrape_leaderboard
        >> load_leaderboard
    )
    (
        wait_for_production_backups
        >> success_alert
    )

