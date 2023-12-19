# huggingface-etl

This repository is designed to scrape data from Hugging Face's API, specifically about Hugging Face models. There is also Hugging Face dataset information but we are not scraping it at this time.

Some relevant notes here:

1. Some models are missing in this process; the missed models appear to be closed or gated models that require having private known information in order to access the model, which is not supported in querying the API. This is a small percentage of models, and they are all catalogued in missed.jsonl after the pipeline runs.
2. Significant portions of the data in the API include user-defined or user-modifiable fields, As a result, these fields do not have consistent formatting, and even sometimes have completely broken formatting (to the extent that if you view the corresponding model page on the Hugging Face website it will not display the model card info at all). To handle these broken fields, we are doing a lot of post-hoc cleaning, but beyond a certain point we're also just dumping the broken fields into strings or json and leaving it to be read if there's interest. This choice has been made because we want code that is durable rather than brittle, and if users are producing new user-defined fields every time we update there's no way for us to keep up or account for all of these error cases.
3. Given how inconsistent typing is in this json, and how often we're having to correct it, we're not using python function typing even though we'd prefer it. Instead, we rely on unit testing to ensure code correctness.

In addition to the models as a whole, we are also scraping Hugging Face's LLM leaderboard. This is not extracted via API, since none appears to exist, but instead scraped directly from their website.

# Deployment

To refresh the docker container (which you must do if you change any of the python scripts), run

```
docker build -t huggingface .
docker tag huggingface us.gcr.io/gcp-cset-projects/huggingface
docker push us.gcr.io/gcp-cset-projects/huggingface
```

To redeploy the airflow pipeline, which you must do if any of the schemas, the SQL, or the airflow DAG changes, run
```
./push_to_airflow
```